const wppconnect = require('@wppconnect-team/wppconnect');
const fs = require('fs');

console.log('🚀 Iniciando WPPConnect...\n');

async function start() {
  try {
    const client = await wppconnect.create({
      session: 'loja-celulares',
      headless: false,
      devtools: false,
      useChrome: true,
      disableWelcome: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
      catchQR: (base64Qr, asciiQR) => {
        console.log('📱 QR CODE GERADO!\n');
        console.log(asciiQR); // Mostra o QR code em ASCII no terminal
        fs.writeFileSync('./qrcode_wpp.txt', base64Qr); // Salva o QR code em base64
        console.log('✓ QR Code salvo em: qrcode_wpp.txt');
        console.log('📸 Escaneie com seu WhatsApp agora!\n');
      },
      logQR: false // Desativa o log padrão do QR code, pois estamos a tratá-lo
    });

    console.log('✅ Cliente criado! Aguardando leitura do QR code e conexão...\n');

    // STATUS CONEXÃO
    client.onStateChange((state) => {
      console.log(`📡 Estado: ${state}\n`);
      if (state === 'CONNECTED') {
        console.log('🎉🎉🎉 CONECTADO COM SUCESSO! 🎉🎉🎉\n');
      }
    });

    // RECEBER MENSAGENS
    client.onMessage(async (message) => {
      console.log('\n--- NOVA MENSAGEM RECEBIDA ---');
      console.log(JSON.stringify(message, null, 2)); // Loga o objeto completo da mensagem

      console.log(`\n📨 Mensagem de ${message.from}:`);
      console.log(`   Texto: ${message.body}\n`);
      console.log(`   De: ${message.from}\n`);
      // Chamar o script Python para processar a pergunta
      const { spawn } = require('child_process');
      if (message.from === '5521980306189@c.us') {
        client.sendText(message.from, '🤖 Processando sua solicitação, aguarde...');
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
          if (code === 0) {
              client.sendText(message.from, scriptOutput);
          } else {
              client.sendText(message.from, 'Desculpe, ocorreu um erro ao processar sua solicitação.');
          }
      });
    }
    });

  } catch (error) {
    console.error('❌ Erro:', error.message);
    process.exit(1);
  }
}

start();