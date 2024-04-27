from flask import Flask, request, render_template, redirect, url_for, session
import re
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ustaw swoją unikalną secret key

def format_ram(total_memory_kb):
    total_memory_gb = total_memory_kb / (1024 * 1024)
    return f"{total_memory_gb:.0f} GB"

def generate_qr_code(data_to_encode):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data_to_encode)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')

    qr_img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return qr_img_base64

@app.route('/chromebook_test', methods=['GET', 'POST'])
def upload_txt():
    if request.method == 'POST':
        file = request.files['file_input']
        file_content = file.read()
        session['file_content'] = file_content
        return redirect(url_for('uzupelnienie_danych'))

    return render_template('upload_txt.html')

@app.route('/uzupelnienie_danych', methods=['GET', 'POST'])
def uzupelnienie_danych():
    if request.method == 'POST':
        test_results = {}
        test_results['Keyboard Test'] = request.form.get('keyboard_test')
        test_results['LCD Test'] = request.form.get('lcd_test')
        test_results['Ports Test'] = request.form.get('ports_test')
        test_results['Visual Test'] = request.form.get('visual_test')
        test_results['Burn-In Test'] = request.form.get('burn_in_test')
        test_results['Battery Test'] = request.form.get('battery_test')
        test_results['Disk Drive Found'] = request.form.get('disk_drive_found')
        session['test_results'] = test_results

        cpu_model = request.form.get('cpu_model')
        total_memory_gb = request.form.get('total_memory_gb')
        wear_percentage = request.form.get('wear_percentage')

        return redirect(url_for('podsumowanie', cpu_model=cpu_model, total_memory_gb=total_memory_gb, wear_percentage=wear_percentage))

    if 'file_content' not in session:
        return redirect(url_for('upload_txt'))

    return render_template('uzupelnienie_danych.html')

@app.route('/podsumowanie', methods=['GET', 'POST'])
def podsumowanie():
    # Odczytujemy dane zapisane w sesji
    dane_z_pliku_bytes = session['file_content']
    dane_z_pliku_str = dane_z_pliku_bytes.decode('utf-8')  # Konwersja z bytes na str

    # Przetwarzamy dane z pliku, na przykład za pomocą wyrażeń regularnych
    cpu_model_match = re.search(r'CpuModel Name: (.+)', dane_z_pliku_str)
    if cpu_model_match:
        cpu_model = cpu_model_match.group(1)
    else:
        cpu_model = "Nie znaleziono informacji o modelu CPU"

    total_memory_match = re.search(r'Total Memory \(kib\): (\d+)', dane_z_pliku_str)
    if total_memory_match:
        total_memory_kb = int(total_memory_match.group(1))
        total_memory_gb = format_ram(total_memory_kb)
    else:
        total_memory_gb = "Nie znaleziono informacji o ilości pamięci RAM"

    wear_percentage_match = re.search(r'Wear Percentage: (\d+)', dane_z_pliku_str)
    if wear_percentage_match:
        wear_percentage = f"{wear_percentage_match.group(1)}%"
    else:
        wear_percentage = "Nie znaleziono informacji o zużyciu baterii"

    # Odczytujemy dane wynikowe z formularza uzupelnienie_danych
    test_results = session.get('test_results', {})

    # Generujemy kod QR na podstawie danych
    qr_data = f"CPU Model: {cpu_model}\nRAM: {total_memory_gb}\nBattery life: {wear_percentage.strip(' %')}\n\nWyniki testów:\n"
    for test_name, test_result in test_results.items():
        qr_data += f"{test_name}: {test_result}\n"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data) 
    qr.make(fit=True)

    # Konwertujemy wygenerowany kod QR na obrazek w formacie PNG
    qr_img = qr.make_image(fill_color="black", back_color="white") 

    # Kodujemy obrazek QR jako base64, aby móc go umieścić bezpośrednio w szablonie HTML
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Przekazujemy dane do szablonu, w tym zakodowany obraz QR jako część kontekstu
    return render_template('podsumowanie.html', cpu_model=cpu_model, total_memory_gb=total_memory_gb, wear_percentage=wear_percentage, test_results=test_results, qr_img_base64=qr_img_base64)


if __name__ == '__main__':
    app.run(debug=True)
