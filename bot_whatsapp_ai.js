const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const { exec } = require('child_process');
const fs = require('fs');

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

client.on('qr', qr => {
    qrcode.toFile('qrcode.png', qr, (err) => {
        if (err) throw err;
        console.log('QR code saved to qrcode.png');
    });
});

client.on('ready', () => {
    console.log('Client is ready!');
});

client.on('message', (message) => {
    console.log(`Message from ${message.from}: ${message.body}`);
    console.log("Corpo da mensagem recebida:", message.body);

    // Chamar o script Python para processar a pergunta
    const { spawn } = require('child_process');
    const pythonProcess = spawn('python', ['ai_agent_whatsapp.py', message.body]);

    let scriptOutput = "";
    pythonProcess.stdout.on('data', (data) => {
        scriptOutput += data.toString();
    });

    let scriptError = "";
    pythonProcess.stderr.on('data', (data) => {
        scriptError += data.toString();
        console.error(`Erro do Python: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Processo Python finalizado com código ${code}`);
        if (code !== 0) {
            console.error(`Python process exited with error. Stderr: ${scriptError}`);
            message.reply('Desculpe, ocorreu um erro ao processar sua mensagem.');
            return;
        }
        const resposta = scriptOutput.trim();
        console.log('Resposta do Python:', resposta);
        message.reply(resposta);
    });
});

client.initialize();