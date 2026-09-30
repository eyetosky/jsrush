from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from provably_fair import ProvablyFairRNG, GameSeedManager, FairnessVerifier
from extensions import redis_client

fairness_bp = Blueprint('fairness', __name__)

# Initialize seed manager
seed_manager = GameSeedManager(redis_client)


@fairness_bp.route('/api/fairness/new-session', methods=['POST'])
@login_required
def new_fair_session():
    """Create a new provably fair game session"""
    data = request.get_json()
    game_type = data.get('game_type')
    client_seed = data.get('client_seed')  # Optional, user can provide
    
    if not game_type:
        return jsonify({'success': False, 'message': 'game_type required'}), 400
    
    valid_games = ['dice', 'roulette', 'crash', 'slots', 'blackjack', 'mines', 'bingo', 'keno', 'wheel', 'videopoker']
    if game_type not in valid_games:
        return jsonify({'success': False, 'message': 'Invalid game type'}), 400
    
    game_seed = seed_manager.create_game_session(str(current_user.id), game_type, client_seed)
    
    return jsonify({
        'success': True,
        'server_seed_hash': ProvablyFairRNG.hash_server_seed(game_seed.server_seed),
        'client_seed': game_seed.client_seed,
        'nonce': game_seed.nonce,
        'game_type': game_type
    })


@fairness_bp.route('/api/fairness/verify', methods=['POST'])
@login_required
def verify_game():
    """Verify a game result"""
    data = request.get_json()
    server_seed = data.get('server_seed')
    server_seed_hash = data.get('server_seed_hash')
    client_seed = data.get('client_seed')
    nonce = data.get('nonce')
    result = data.get('result')
    game_type = data.get('game_type')
    
    if not all([server_seed, server_seed_hash, client_seed, nonce is not None, result, game_type]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    
    verification = FairnessVerifier.verify_game(
        server_seed, server_seed_hash, client_seed, nonce, result, game_type
    )
    
    return jsonify({
        'success': True,
        'verification': verification
    })


@fairness_bp.route('/api/fairness/roll', methods=['POST'])
@login_required
def fair_roll():
    """Generate a provably fair roll for a game action"""
    data = request.get_json()
    game_type = data.get('game_type')
    action = data.get('action', 'roll')  # roll, hit, spin, etc.
    
    if not game_type:
        return jsonify({'success': False, 'message': 'game_type required'}), 400
    
    game_seed = seed_manager.get_game_seed(game_type, str(current_user.id))
    if not game_seed:
        return jsonify({'success': False, 'message': 'No active session. Create session first.'}), 400
    
    nonce = game_seed.nonce
    
    # Generate result based on game type
    if game_type == 'dice':
        result = {'dice': list(ProvablyFairRNG.roll_dice(game_seed.server_seed, game_seed.client_seed, nonce))}
    elif game_type == 'roulette':
        result = {'number': ProvablyFairRNG.roll_roulette(game_seed.server_seed, game_seed.client_seed, nonce)}
    elif game_type == 'crash':
        result = {'crash_point': ProvablyFairRNG.roll_crash(game_seed.server_seed, game_seed.client_seed, nonce)}
    elif game_type == 'slots':
        result = {'reels': ProvablyFairRNG.spin_slots(game_seed.server_seed, game_seed.client_seed, nonce)}
    elif game_type == 'blackjack':
        if action == 'deal':
            result = ProvablyFairRNG.deal_blackjack(game_seed.server_seed, game_seed.client_seed, nonce)
        elif action == 'hit':
            hit_count = data.get('hit_count', 1)
            result = {'card': ProvablyFairRNG.hit_card(game_seed.server_seed, game_seed.client_seed, nonce, hit_count)}
        else:
            return jsonify({'success': False, 'message': 'Invalid action for blackjack'}), 400
    elif game_type == 'mines':
        mine_count = data.get('mine_count', 3)
        result = {'mines': ProvablyFairRNG.place_mines(game_seed.server_seed, game_seed.client_seed, nonce, 25, mine_count)}
    elif game_type == 'bingo':
        result = {'number': ProvablyFairRNG.call_bingo(game_seed.server_seed, game_seed.client_seed, nonce)}
    elif game_type == 'keno':
        result = {'drawn': ProvablyFairRNG.draw_keno(game_seed.server_seed, game_seed.client_seed, nonce)}
    elif game_type == 'wheel':
        segments = data.get('segments', [1,2,3,5,10,20,0,0,0.5,0.5])
        result = {'multiplier': ProvablyFairRNG.spin_wheel(game_seed.server_seed, game_seed.client_seed, nonce, segments)}
    elif game_type == 'videopoker':
        if action == 'deal':
            result = {'hand': ProvablyFairRNG.deal_cards(game_seed.server_seed, game_seed.client_seed, nonce, 5)}
        elif action == 'draw':
            hold_indices = data.get('hold_indices', [])
            # For draw, we'd need more complex logic
            result = {'new_cards': []}
        else:
            return jsonify({'success': False, 'message': 'Invalid action for videopoker'}), 400
    else:
        return jsonify({'success': False, 'message': 'Unsupported game type'}), 400
    
    # Increment nonce for next action
    new_nonce = seed_manager.increment_nonce(game_type, str(current_user.id))
    
    return jsonify({
        'success': True,
        'result': result,
        'nonce': nonce,
        'next_nonce': new_nonce,
        'server_seed_hash': ProvablyFairRNG.hash_server_seed(game_seed.server_seed)
    })


@fairness_bp.route('/api/fairness/reveal-seed', methods=['POST'])
@login_required
def reveal_seed():
    """Reveal server seed after game session ends (for verification)"""
    data = request.get_json()
    game_type = data.get('game_type')
    
    if not game_type:
        return jsonify({'success': False, 'message': 'game_type required'}), 400
    
    game_seed = seed_manager.get_game_seed(game_type, str(current_user.id))
    if not game_seed:
        return jsonify({'success': False, 'message': 'No active session'}), 400
    
    server_seed = game_seed.server_seed
    
    # End the session
    seed_manager.end_game_session(game_type, str(current_user.id))
    
    return jsonify({
        'success': True,
        'server_seed': server_seed,
        'server_seed_hash': ProvablyFairRNG.hash_server_seed(server_seed),
        'client_seed': game_seed.client_seed,
        'final_nonce': game_seed.nonce
    })


@fairness_bp.route('/api/fairness/current-session', methods=['GET'])
@login_required
def current_session():
    """Get current game session info (without revealing server seed)"""
    game_type = request.args.get('game_type')
    
    if not game_type:
        return jsonify({'success': False, 'message': 'game_type required'}), 400
    
    game_seed = seed_manager.get_game_seed(game_type, str(current_user.id))
    if not game_seed:
        return jsonify({'success': False, 'message': 'No active session', 'has_session': False})
    
    return jsonify({
        'success': True,
        'has_session': True,
        'client_seed': game_seed.client_seed,
        'nonce': game_seed.nonce,
        'server_seed_hash': ProvablyFairRNG.hash_server_seed(game_seed.server_seed),
        'game_type': game_type
    })