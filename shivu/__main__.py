import importlib
import time
import random
import re
import asyncio
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import (
    collection, top_global_groups_collection, group_user_totals_collection,
    user_collection, user_totals_collection, shivuu, application,
    SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
)
from shivu.modules import ALL_MODULES

# Initialize data structures
locks = {}
message_counts = {}
last_user = {}
warned_users = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}

# Load all modules
for module_name in ALL_MODULES:
    try:
        imported_module = importlib.import_module(f"shivu.modules.{module_name}")
    except ImportError as e:
        LOGGER.error(f"Failed to import module {module_name}: {e}")

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext) -> None:
    if not update.message or not update.effective_chat:
        return

    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    # Initialize lock if not exists
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    
    async with lock:
        
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 10)
        else:
            message_frequency = 10

        
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
            
                if user_id in warned_users and time.time() - warned_users[user_id] < 60:
                    return
                else:
                    
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be ignored for 1 Minute...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

    
        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

    
        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            
            message_counts[chat_id] = 0

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    
    try:
        all_characters = list(await collection.find({}).to_list(length=None))
        
        # Initialize sent characters list if not exists
        if chat_id not in sent_characters:
            sent_characters[chat_id] = []

        # Reset if all characters have been sent
        if len(sent_characters[chat_id]) >= len(all_characters):
            sent_characters[chat_id] = []

        # Select a new character
        available_chars = [c for c in all_characters if c['id'] not in sent_characters[chat_id]]
        if not available_chars:
            return
            
        character = random.choice(available_chars)
        sent_characters[chat_id].append(character['id'])
        last_characters[chat_id] = character

        # Reset correct guesses
        if chat_id in first_correct_guesses:
            del first_correct_guesses[chat_id]

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=f"""A New {character['rarity']} Character Appeared...\n/guess Character Name and add in Your Harem""",
            parse_mode='Markdown'
        )
    except Exception as e:
        LOGGER.error(f"Error in send_image: {e}")

async def guess(update: Update, context: CallbackContext) -> None:
    if not update.message or not update.effective_chat:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    try:
        # Check if there's a character to guess
        if chat_id not in last_characters:
            await update.message.reply_text('No character to guess right now!')
            return

        # Check if already guessed
        if chat_id in first_correct_guesses:
            await update.message.reply_text('❌️ Already Guessed By Someone.. Try Next Time')
            return

        # Validate guess
        guess = ' '.join(context.args).lower() if context.args else ''
        if "()" in guess or "&" in guess.lower():
            await update.message.reply_text("Nahh You Can't use This Types of words in your guess..❌️")
            return

        # Prepare character name parts
        character = last_characters[chat_id]
        name_parts = character['name'].lower().split()

        # Check if guess is correct
        if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
            first_correct_guesses[chat_id] = user_id

            # Update user data
            await update_user_data(user_id, update, character)
            
            # Update group user totals
            await update_group_user_data(user_id, chat_id, update)
            
            # Update global group stats
            await update_global_group_data(chat_id, update)

            # Prepare response
            keyboard = [[InlineKeyboardButton(
                "See Harem", 
                switch_inline_query_current_chat=f"collection.{user_id}"
            )]]

            await update.message.reply_text(
                f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> '
                f'You Guessed a New Character ✅️\n\n'
                f'𝗡𝗔𝗠𝗘: <b>{character["name"]}</b>\n'
                f'𝗔𝗡𝗜𝗠𝗘: <b>{character["anime"]}</b>\n'
                f'𝗥𝗔𝗜𝗥𝗧𝗬: <b>{character["rarity"]}</b>\n\n'
                'This Character added in Your harem.. use /harem To see your harem',
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text('Please Write Correct Character Name... ❌️')
    except Exception as e:
        LOGGER.error(f"Error in guess handler: {e}")
        await update.message.reply_text('An error occurred while processing your guess.')

async def update_user_data(user_id: int, update: Update, character: dict):
    user = await user_collection.find_one({'id': user_id})
    update_fields = {}
    
    if hasattr(update.effective_user, 'username'):
        update_fields['username'] = update.effective_user.username
    if update.effective_user.first_name:
        update_fields['first_name'] = update.effective_user.first_name
    
    if user:
        if update_fields:
            await user_collection.update_one({'id': user_id}, {'$set': update_fields})
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    else:
        user_data = {
            'id': user_id,
            'characters': [character],
            **update_fields
        }
        await user_collection.insert_one(user_data)

async def update_group_user_data(user_id: int, chat_id: int, update: Update):
    group_user_data = {
        'user_id': user_id,
        'group_id': chat_id,
        'count': 1
    }
    
    if hasattr(update.effective_user, 'username'):
        group_user_data['username'] = update.effective_user.username
    if update.effective_user.first_name:
        group_user_data['first_name'] = update.effective_user.first_name
    
    await group_user_totals_collection.update_one(
        {'user_id': user_id, 'group_id': chat_id},
        {'$inc': {'count': 1}, '$set': group_user_data},
        upsert=True
    )

async def update_global_group_data(chat_id: int, update: Update):
    if update.effective_chat and update.effective_chat.title:
        await top_global_groups_collection.update_one(
            {'group_id': chat_id},
            {
                '$inc': {'count': 1},
                '$set': {'group_name': update.effective_chat.title}
            },
            upsert=True
        )

async def fav(update: Update, context: CallbackContext) -> None:
    if not update.message or not context.args:
        await update.message.reply_text('Please provide Character id...')
        return

    user_id = update.effective_user.id
    character_id = context.args[0]

    try:
        user = await user_collection.find_one({'id': user_id})
        if not user:
            await update.message.reply_text('You have not Guessed any characters yet....')
            return

        character = next((c for c in user.get('characters', []) if c['id'] == character_id), None)
        if not character:
            await update.message.reply_text('This Character is Not In your collection')
            return

        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'favorites': [character_id]}}
        )

        await update.message.reply_text(
            f'Character {character["name"]} has been added to your favorites...'
        )
    except Exception as e:
        LOGGER.error(f"Error in fav handler: {e}")
        await update.message.reply_text('An error occurred while updating favorites.')

def main() -> None:
    """Run bot."""
    # Add handlers
    application.add_handler(CommandHandler(
        ["guess", "protecc", "collect", "grab", "hunt"], guess, block=False
    ))
    application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))

    # Start the bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
