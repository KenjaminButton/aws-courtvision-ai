#!/usr/bin/env python3
"""
add_game_media.py - Add Reddit thread, YouTube links, and game context to games

Usage:
    python3 add_game_media.py --game 401818635 --reddit "https://reddit.com/..." --highlights "https://youtube.com/..." --postgame "https://youtube.com/..."
    python3 add_game_media.py --game 401818635 --context "Iowa (#11) hosts unranked Lindenwood..."
    python3 add_game_media.py --list 2026  # List all games and their media URLs
"""

import boto3
import argparse
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')


def add_media(game_id: str, reddit_url: str = None, highlights_url: str = None, postgame_url: str = None, context: str = None):
    """Add or update media URLs and context for a game."""
    update_parts = []
    expr_values = {}
    
    if reddit_url:
        update_parts.append('reddit_thread_url = :reddit')
        expr_values[':reddit'] = reddit_url
    
    if highlights_url:
        update_parts.append('youtube_highlights_url = :highlights')
        expr_values[':highlights'] = highlights_url
    
    if postgame_url:
        update_parts.append('youtube_postgame_url = :postgame')
        expr_values[':postgame'] = postgame_url
    
    if context:
        update_parts.append('game_context = :context')
        expr_values[':context'] = context
    
    if not update_parts:
        print("❌ No data provided. Use --reddit, --highlights, --postgame, and/or --context")
        return False
    
    try:
        # First verify the game exists
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
        )
        
        if 'Item' not in response:
            print(f"❌ Game {game_id} not found in database")
            return False
        
        game = response['Item']
        opponent = game.get('opponent', {}).get('name', 'Unknown')
        date = game.get('date', '').split('T')[0]
        
        # Update the game
        table.update_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'},
            UpdateExpression='SET ' + ', '.join(update_parts),
            ExpressionAttributeValues=expr_values
        )
        
        print(f"✅ Updated: {date} vs {opponent} (ID: {game_id})")
        if reddit_url:
            print(f"   📱 Reddit: {reddit_url[:60]}...")
        if highlights_url:
            print(f"   🎬 Highlights: {highlights_url[:60]}...")
        if postgame_url:
            print(f"   🎙️ Post-game: {postgame_url[:60]}...")
        if context:
            print(f"   📝 Context: {context[:60]}...")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error: {e}")
        return False


def list_games(season: int):
    """List all games and their media URLs for a season."""
    try:
        response = table.query(
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={':pk': f'SEASON#{season}'}
        )
        
        games = sorted(response.get('Items', []), key=lambda x: x.get('date', ''))
        
        print(f"\n🏀 Iowa Hawkeyes {season-1}-{str(season)[2:]} Season\n")
        print(f"{'Date':<12} {'Opponent':<20} {'Game ID':<12} {'Reddit':<8} {'Highlights':<11} {'Postgame':<9} {'Context':<8}")
        print("-" * 90)
        
        for game in games:
            if not game.get('status_completed'):
                continue
                
            game_id = game.get('game_id', '')
            date = game.get('date', '').split('T')[0]
            opponent = game.get('opponent_abbrev', 'UNK')
            
            # Fetch METADATA to check for media URLs
            meta_response = table.get_item(
                Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
            )
            meta = meta_response.get('Item', {})
            
            has_reddit = '✅' if meta.get('reddit_thread_url') else '❌'
            has_highlights = '✅' if meta.get('youtube_highlights_url') else '❌'
            has_postgame = '✅' if meta.get('youtube_postgame_url') else '❌'
            has_context = '✅' if meta.get('game_context') else '❌'
            
            print(f"{date:<12} {opponent:<20} {game_id:<12} {has_reddit:<8} {has_highlights:<11} {has_postgame:<9} {has_context:<8}")
        
        print()
        
    except ClientError as e:
        print(f"❌ Error: {e}")


def show_context(game_id: str):
    """Show the current context for a game."""
    try:
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
        )
        
        if 'Item' not in response:
            print(f"❌ Game {game_id} not found")
            return
        
        game = response['Item']
        opponent = game.get('opponent', {}).get('name', 'Unknown')
        date = game.get('date', '').split('T')[0]
        context = game.get('game_context', 'No context set')
        
        print(f"\n📝 Context for {date} vs {opponent} (ID: {game_id}):\n")
        print("-" * 60)
        print(context)
        print("-" * 60)
        print()
        
    except ClientError as e:
        print(f"❌ Error: {e}")


def remove_media(game_id: str, remove_reddit: bool = False, remove_highlights: bool = False, remove_postgame: bool = False, remove_context: bool = False):
    """Remove media URLs or context from a game."""
    remove_parts = []
    
    if remove_reddit:
        remove_parts.append('reddit_thread_url')
    if remove_highlights:
        remove_parts.append('youtube_highlights_url')
    if remove_postgame:
        remove_parts.append('youtube_postgame_url')
    if remove_context:
        remove_parts.append('game_context')
    
    if not remove_parts:
        print("❌ Specify --remove-reddit, --remove-highlights, --remove-postgame, and/or --remove-context")
        return False
    
    try:
        table.update_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'},
            UpdateExpression='REMOVE ' + ', '.join(remove_parts)
        )
        print(f"✅ Removed {', '.join(remove_parts)} from game {game_id}")
        return True
    except ClientError as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Add Reddit/YouTube links and game context to game records',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add media URLs to a game
  python3 add_game_media.py --game 401818635 \\
    --reddit "https://www.reddit.com/r/NCAAW/comments/..." \\
    --highlights "https://www.youtube.com/watch?v=..." \\
    --postgame "https://www.youtube.com/watch?v=..."

  # Add game context for AI summary
  python3 add_game_media.py --game 401818635 --context "Iowa (#11) hosts unranked Lindenwood...

STARTERS THIS GAME:
- Hannah Stuelke (Senior, Forward)
- Ava Heiden (Sophomore, Center)
...

GAME NOTES:
This is Iowa's final home game before..."

  # List all games and their media/context status
  python3 add_game_media.py --list 2026

  # Show current context for a game
  python3 add_game_media.py --game 401818635 --show-context

  # Remove context
  python3 add_game_media.py --game 401818635 --remove-context
        """
    )
    
    parser.add_argument('--game', type=str, help='Game ID (e.g., 401818635)')
    parser.add_argument('--reddit', type=str, help='Reddit game thread URL')
    parser.add_argument('--highlights', type=str, help='YouTube highlights video URL (Big Ten Network)')
    parser.add_argument('--postgame', type=str, help='YouTube post-game show URL')
    parser.add_argument('--context', type=str, help='Game context for AI summary (starters, storylines, etc.)')
    parser.add_argument('--list', type=int, metavar='SEASON', help='List games for season (e.g., 2026)')
    parser.add_argument('--show-context', action='store_true', help='Show current context for a game')
    parser.add_argument('--remove-reddit', action='store_true', help='Remove Reddit URL')
    parser.add_argument('--remove-highlights', action='store_true', help='Remove highlights URL')
    parser.add_argument('--remove-postgame', action='store_true', help='Remove post-game URL')
    parser.add_argument('--remove-context', action='store_true', help='Remove game context')
    
    args = parser.parse_args()
    
    if args.list:
        list_games(args.list)
    elif args.game:
        if args.show_context:
            show_context(args.game)
        elif args.remove_reddit or args.remove_highlights or args.remove_postgame or args.remove_context:
            remove_media(args.game, args.remove_reddit, args.remove_highlights, args.remove_postgame, args.remove_context)
        else:
            add_media(args.game, args.reddit, args.highlights, args.postgame, args.context)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()