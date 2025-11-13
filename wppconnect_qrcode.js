const wppconnect = require('@wppconnect-team/wppconnect');
const fs = require('fs');
const axios = require('axios'); // Adicionado axios

console.log('🚀 Iniciando WPPConnect...\n');

async function start() {
  try {
    const client = await wppconnect.create({
      session: 'loja-celulares',
      headless: true,
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
      // Ignorar mensagens de status, grupos e que não sejam de texto
      if (message.isStatus || message.isGroupMsg || !message.body) {
        return;
      }

      console.log('\n--- NOVA MENSAGEM RECEBIDA ---');
      console.log(`\n📨 Mensagem de ${message.from}:`);
      console.log(`   Texto: ${message.body}\n`);

      try {
        // Envia a mensagem para o webhook do Flask
        const response = await axios.post('http://localhost:5000/webhook', {
          message: message.body
        });

        // Envia a resposta do agente de IA de volta para o usuário
        if (response.data && response.data.response) {
          client.sendText(message.from, response.data.response);
        } else {
          client.sendText(message.from, 'Desculpe, não consegui obter uma resposta.');
        }
      } catch (error) {
        console.error('❌ Erro ao contatar o webhook:', error.message);
        client.sendText(message.from, 'Desculpe, ocorreu um erro ao processar sua solicitação.');
      }
    });

  } catch (error) {
    console.error('❌ Erro:', error.message);
    process.exit(1);
  }
}

start();