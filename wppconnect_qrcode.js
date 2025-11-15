const wppconnect = require('@wppconnect-team/wppconnect');
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const { exec } = require('child_process');

// --- Configuração --- 
const PORT = 3000;
const FLASK_WEBHOOK_URL = 'http://localhost:5001/webhook';
const SESSION_NAME = 'loja-celulares';

const app = express();
app.use(express.json());

let wppClient;
let botId;

console.log('🚀 Iniciando o Servidor WPPConnect com Express...');

// Endpoint para receber as respostas processadas pelo Python
app.post('/process-response', async (req, res) => {
    if (!wppClient) {
        console.error('🚨 Cliente WPP não está pronto para receber respostas.');
        return res.status(503).json({ error: 'Cliente WPP não inicializado.' });
    }

    const responsePayload = req.body;
    console.log('\n--- RESPOSTA RECEBIDA DO PYTHON ---');
    console.log(JSON.stringify(responsePayload, null, 2));

    const { tipo, recipient_phone } = responsePayload;

    if (!recipient_phone) {
        console.error('🚨 Erro: Número do destinatário não fornecido pelo Python.');
        return res.status(400).json({ error: 'Número do destinatário ausente.' });
    }

    try {
        if (tipo === 'texto') {
            await wppClient.sendText(recipient_phone, responsePayload.conteudo);
            console.log(`✓ Mensagem de texto enviada para ${recipient_phone}`);
        } else if (tipo === 'fotos') {
            const { fotos, legenda } = responsePayload;
            for (const fotoPath of fotos) {
                try {
                    if (/^https?:\/\//i.test(fotoPath)) {
                        await wppClient.sendImage(recipient_phone, fotoPath, 'smartphone.jpg', legenda);
                        console.log(`✓ Imagem remota (${fotoPath}) enviada para ${recipient_phone}`);
                    } else {
                        await wppClient.sendImage(recipient_phone, fotoPath, 'smartphone.jpg', legenda);
                        console.log(`✓ Imagem local (${fotoPath}) enviada para ${recipient_phone}`);
                    }
                } catch (e) {
                    console.error(`🚨 Falha ao enviar imagem (${fotoPath}):`, e.message);
                    try {
                        await wppClient.sendImage(recipient_phone, fotoPath, 'smartphone.jpg', legenda);
                        console.log(`✓ Tentativa de fallback com caminho direto (${fotoPath}) bem-sucedida.`);
                    } catch (fallbackError) {
                        console.error(`🚨 Falha no fallback com caminho direto para ${fotoPath}:`, fallbackError.message);
                    }
                }
            }
        } else {
            console.warn(`⚠️ Tipo de resposta desconhecido: ${tipo}`);
        }
        res.status(200).json({ status: 'success' });
    } catch (error) {
        console.error(`🚨 Erro ao enviar resposta para ${recipient_phone}:`, error.message);
        res.status(500).json({ error: 'Falha ao enviar mensagem/imagem no WhatsApp.' });
    }
});

// Função para iniciar o cliente WPPConnect
async function startWppClient() {
    try {
        wppClient = await wppconnect.create({
            session: SESSION_NAME,
            headless: false,
            devtools: false,
            useChrome: true,
            disableWelcome: true,
            args: ['--no-sandbox', '--disable-dev-shm-usage'],
            catchQR: (base64Qr, asciiQR) => {
                console.log('📱 QR CODE GERADO!');
                console.log(asciiQR);
                try {
                    fs.writeFileSync('./qrcode.png', base64Qr.replace('data:image/png;base64,', ''), 'base64');
                    console.log('✓ QR Code salvo em: qrcode.png');
                    const imgPath = `${__dirname}\\qrcode.png`;
                    exec(`start "" "${imgPath}"`);
                    console.log('🖼️ Abrindo QR code no visualizador padrão...');
                } catch (e) {
                    console.error('❌ Falha ao salvar/abrir qrcode.png:', e.message);
                }
            },
            logQR: false
        });

        console.log('✅ Cliente WPP criado! Aguardando conexão...');

        // Aguarda a conexão e obtém o botId ANTES de registrar o listener
        wppClient.onStateChange(async (state) => {
            console.log(`📡 Estado do WPP: ${state}`);
            if (state === 'CONNECTED') {
                try {
                    const hostDevice = await wppClient.getHostDevice();
                    if (hostDevice && hostDevice.id && hostDevice.id._serialized) {
                        botId = hostDevice.id._serialized;
                        console.log('🎉🎉🎉 CONECTADO COM SUCESSO AO WHATSAPP! 🎉🎉🎉');
                        console.log(`   ID do Bot: ${botId}\n`);
                    } else {
                        console.error('⚠️ Não foi possível obter o ID do bot');
                    }
                } catch (err) {
                    console.error('❌ Erro ao obter ID do bot:', err.message);
                }
                try {
                    await wppClient.sendText('5511915022668@c.us', 'Renato Tanner online. Sistema restaurado. Pode enviar as perguntas.');
                    console.log('✓ Mensagem de confirmação enviada para 5511915022668');
                } catch (sendErr) {
                    console.error('⚠️ Falha ao enviar mensagem de confirmação:', sendErr.message);
                }
            }
        });

        // Listener para novas mensagens
        wppClient.onMessage(async (message) => {
            // Ignora se for atualização de status ou não tiver corpo
            if (message.isStatus || !message.body) {
                return;
            }

            const ts = new Date().toLocaleString('pt-BR');
            const messageBody = message.body.toLowerCase();
            
            // Log detalhado para debug de grupos
            if (message.isGroupMsg) {
                console.log(`\n--- MENSAGEM DE GRUPO RECEBIDA ---`);
                console.log(`🕒 ${ts}`);
                console.log(`👥 Grupo: ${message.from}`);
                console.log(`👤 Autor: ${message.author}`);
                console.log(`📱 Bot ID: ${botId || 'AINDA NÃO DEFINIDO'}`);
                console.log(`📝 Texto: ${message.body}`);
                console.log(`🔔 Menções: ${JSON.stringify(message.mentionedJidList)}`);
                console.log(`❓ Bot mencionado: ${message.mentionedJidList && botId ? message.mentionedJidList.includes(botId) : 'N/A'}\n`);
            }

            // Se for mensagem de grupo, só processa se o bot tiver ID e for mencionado
            if (message.isGroupMsg) {
                // Verificar se bot está pronto
                if (!botId) {
                    console.log(`⏳ Bot ainda não está pronto; usando fallback de menção/nome`);
                }
                
                // Verificar menção direta (@nome)
                const botMentioned = (botId && message.mentionedJidList && message.mentionedJidList.includes(botId)) || (message.mentionedJidList && message.mentionedJidList.length > 0);
                
                // Verificar se o nome do bot aparece no texto (fallback)
                // Usa regex para match exato de palavras
                const botNameMentioned = /\b(renato|phones\s+paraguay)\b/i.test(messageBody);
                
                // Verificar se é resposta a uma mensagem do bot
                const isReplyToBot = message.quotedMsg && message.quotedMsg.fromMe;
                
                if (!botMentioned && !botNameMentioned && !isReplyToBot) {
                    console.log(`🚫 Bot não mencionado no grupo, ignorando`);
                    return;
                }
                
                console.log(`✅ Bot mencionado no grupo! Processando mensagem...`);
            }

            console.log('\n--- NOVA MENSAGEM RECEBIDA DO WHATSAPP ---');
            console.log(`🕒 ${ts}`);
            console.log(`📨 De: ${message.from}`);
            console.log(`   Texto: ${message.body}\n`);

            try {
                // Encaminha o payload simplificado para o servidor Flask
                const payload = {
                    from: message.from,
                    body: message.body,
                    isGroupMsg: message.isGroupMsg,
                    author: message.author || message.from,
                    mentionedJidList: message.mentionedJidList || [],
                    isBotMentioned: message.mentionedJidList && botId ? message.mentionedJidList.includes(botId) : false
                };
                if (message.isMedia && (message.type === 'image' || (message.mimetype && message.mimetype.startsWith('image')))) {
                    try {
                        const buffer = await wppClient.decryptFile(message);
                        payload.media_base64 = `data:${message.mimetype || 'image/jpeg'};base64,${buffer.toString('base64')}`;
                        payload.mimetype = message.mimetype || 'image/jpeg';
                    } catch (e) {
                        console.warn('⚠️ Falha ao obter mídia para OCR:', e.message);
                    }
                }
                
                try {
                    await axios.post(FLASK_WEBHOOK_URL, payload, { headers: { 'Content-Type': 'application/json' } });
                    console.log(`✓ [${ts}] Mensagem encaminhada para o Flask: ${FLASK_WEBHOOK_URL}`);
                } catch (primaryErr) {
                    console.error(`❌ [${ts}] Erro primário ao encaminhar para Flask (${FLASK_WEBHOOK_URL}):`, primaryErr.message);
                    // Tentar novamente em 500ms
                    await new Promise(r => setTimeout(r, 500));
                    try {
                        await axios.post(FLASK_WEBHOOK_URL, payload, { headers: { 'Content-Type': 'application/json' } });
                        console.log(`✓ [${ts}] Reenvio bem-sucedido para o Flask: ${FLASK_WEBHOOK_URL}`);
                    } catch (retryErr) {
                        console.error(`❌ [${ts}] Reenvio falhou (${FLASK_WEBHOOK_URL}):`, retryErr.message);
                        const fallbackUrl = 'http://127.0.0.1:5000/webhook';
                        console.warn(`⚠️ [${ts}] Tentando fallback em ${fallbackUrl}...`);
                        await axios.post(fallbackUrl, payload, { headers: { 'Content-Type': 'application/json' } });
                        console.log(`✓ [${ts}] Mensagem encaminhada via fallback: ${fallbackUrl}`);
                    }
                }
            } catch (error) {
                console.error(`❌ [${ts}] Erro ao encaminhar para Flask:`, error.message);
                if (!message.isGroupMsg) {
                    const lower = (message.body || '').toLowerCase();
                    let reply = 'Estou aqui. Me diz o modelo exato para te responder com dados reais.';
                    if (/(nfc|aproximação|apple pay|google pay|samsung pay)/i.test(lower)) {
                        reply = 'Confiro NFC por modelo específico. Me diz o modelo (ex.: iPhone 15 Pro, Galaxy A54).';
                    } else if (/(dual sim|dois chips|2 chips|esim|e-sim)/i.test(lower)) {
                        reply = 'Dual SIM/eSIM depende da variante. Me diz o modelo para confirmar.';
                    } else if (/(câmera|camera|foto|imagens)/i.test(lower)) {
                        reply = 'Te passo qualidade real de câmera por modelo. Qual aparelho você quer?';
                    } else if (/(preço|valor|custa|parcelar|parcelamento)/i.test(lower)) {
                        reply = 'Te passo preço real de mercado e opções. Qual modelo você está vendo?';
                    }
                    await wppClient.sendText(message.from, reply);
                }
            }
        });

    } catch (error) {
        console.error('❌ Erro crítico ao iniciar o WPPConnect:', error.message);
        process.exit(1);
    }
}

// Inicia o servidor Express e o cliente WPP
app.listen(PORT, () => {
    console.log(`\n✅ Servidor Express rodando na porta ${PORT}`);
    console.log('   Aguardando requisições do Python em /process-response');
    startWppClient();
});