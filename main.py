#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# VERSÃO 2.0 DO BOT DE BOAS VINDAS DO GRUPO DO PODCAST VOLT AMPERE NO TELEGRAM #
#-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+#
# AUTORES: ROGER MANRIQUE E ADRIAN LEMOS                                       #
# DATA: ABRIL DE 2020                                                          #
# IDENTAÇÃO: 3 ESPAÇOS (CUIDADO QUE O NOTEPAD++ TENDE A COLOCAR TAB)           #
# LICENÇA: AGPL                                                                #
################################################################################

# FUNÇÕES (P - PENDENTE, C - CODIFICADA, T - TESTADA)
# [T] IDENTIFICAÇÃO DE NOVO MEMBRO NO GRUPO
# [T] VERIFICAR SE NOVO MEMBRO É UM BOT (FLAG DO TELEPOT) E EXPULSÁ-LO CASO AFIRMATIVO
# [T] CAPTCHA SIMPLES PARA TESTAR SE NOVO MEMBRO É SPAMMER
# [T] TIMEOUT PARA EXPULSÃO CASO NÃO RESPONDA O CAPTCHA
# [T] VERIFICAR SAÍDA DE MEMBROS
# [T] VERIFICAR FEED DO PODCAST
# [P] INTERPRETADOR DE LINGUAGEM NATURAL

# OBS.: FUNÇÃO DE MONTAGEM DE VITRINE PARA O EPISÓDIO TRANSFERIDA PARA OUTRO BOT

import config, mensagem
import telepot, time, feedparser, subprocess, shlex, logging
import apiai, json
import re
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telepot.loop import OrderedWebhook

# inicializa token do bot
bot = telepot.Bot(config.token_bot)

# inicializa variável de novo membro para captcha
DadosNovoMembro = {'chatid':0, 'memberid':0}

def handle(msg):
   # imprime a mensagem
   print "%s\n" % msg
   
   # pega os dados básicos da mensagem 
   content_type, chat_type, chatid = telepot.glance(msg)
   print 'content_type: %s\n' % content_type
   print 'chat_type: %s\n' % chat_type
   try:
      msg['reply_to_message']
      IsReply = 1
      ReplyPara = msg['reply_to_message']['from']['username']
   except:
      IsReply = 0

   print 'IsReply = %d' % IsReply
   
   # caso seja alguém entrando no grupo, envia mensagem de boas vindas
   if content_type == 'new_chat_member':
      # se o novo participante for um bot já expulsa.
      if msg['new_chat_participant']['is_bot']:
         bot.sendMessage(chatid, mensagem.userbot)
         bot.kickChatMember(chatid, msg['new_chat_participant']['id'])
      # se o novo participante não for um bot tenta ver se ele tem um nome.
      else:
         try:
            NomeNovoMembro = msg['new_chat_participant']['first_name']
         except:
            NomeNovoMembro = u'Sem Nome'
         # verifica se o novo membro é um ser humano fazendo um teste simples, perguntando quanto é 2+2
         bot.sendMessage(chatid, u'Olá, ' + NomeNovoMembro + u'. Antes de te dar boas vindas vou verificar se tu é realmente uma pessoa, ok? Quanto é dois mais dois? Você tem 30 segundos para responder.')
         DadosNovoMembro['memberid'] = msg['new_chat_participant']['id']
         DadosNovoMembro['chatid'] = chatid
		 
   # avisa quando alguém deixa o grupo
   elif content_type == 'left_chat_member':
      # tenta ler o nome de quem saiu
      try:
         NomeMembroSaindo = msg['left_chat_participant']['first_name']
      except:
         NomeMembroSaindo = u'Sem Nome'
		 
      # avisa grupo que membro saiu
      bot.sendMessage(chatid, NomeMembroSaindo + mensagem.tchau)
		 
   ###########################################
   # A PARTIR DESSE PONTO ELE DETECTA TEXTOS #
   ###########################################
   elif content_type == 'text':
      # todas as mensagens são convertida para caracteres minúsculos
      MensagemGrupo = msg['text'].lower()
      
	  # se a flag de novo membro estiver ativa e esse cara respondeu corretamente, zera o timeout para kick
      if (MensagemGrupo.find('4') >= 0 or MensagemGrupo.find('quatro') >= 0) and msg['from']['id'] == DadosNovoMembro['memberid']:
         DadosNovoMembro['memberid'] = 0
         DadosNovoMembro['chatid'] = 0
         bot.sendMessage(chatid, u'Agora sim. ' + mensagem.boasvindas)
      
      # comando /boo
      elif MensagemGrupo == '/boo':
         bot.sendMessage(chatid, mensagem.boo)

      # comando /sai
      elif MensagemGrupo == '/oi':
         bot.sendMessage(chatid, mensagem.saudacao)

      #verifica se a menssagem é para o Fauro e envia a menssagem para o DialogFlow
      #elif MensagemGrupo != False and bool(re.search('\\@FauroIA_bot\\b', MensagemGrupo, re.IGNORECASE)):
      elif ((IsReply and ReplyPara == u'FauroIA_bot') or bool(re.search('\\@FauroIA_bot\\b', MensagemGrupo, re.IGNORECASE))):
         MensagemGrupoModificada = MensagemGrupo.replace('@fauroia_bot','') #remove da menssagem o nome do Bot
         request = apiai.ApiAI(config.token_dialogflow).text_request() # Conecta ao Dialogflow através da API Token
         request.lang = 'pt-BR' # Seta a lingua a ser utilizada no dialogflow
         request.session_id = 'Small-Talk' # ID Sessão de Dialogo (para terinamento do bot)
         request.query = MensagemGrupoModificada# Envia a menssagem para o dialogflow 
         responseJson = json.loads(request.getresponse().read().decode('utf-8'))
         response = responseJson['result']['fulfillment']['speech'] # pega a resposta do JSON
         if response:
            bot.sendMessage(chatid, text=response) #Resposta a ser enviada para o BOT

      # comando para mostrar último episódio do feed do podcast
      elif MensagemGrupo == '/ultimo':
         feed = feedparser.parse(config.url_feed)
         # imprime o status do feed (códigos http, exemplo, 404 é feed não encontrado. 200 é ok e 301 é redirecionado)
         print feed.status
         if feed.status == 200 or feed.status == 301:
            print feed.entries[0].links[1].href
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text = u'Ouvir', url = feed.entries[0].links[1].href, callback_data='url')],
            ])
            bot.sendMessage(chatid, feed.entries[0].title, reply_markup=keyboard)

# roda o bot como thread em segundo plano
MessageLoop(bot, handle).run_as_thread()

# avisa o adrian que o bot foi iniciado no servidor
# só funciona se tu já tiveres dado /start no bot em pvt
#bot.sendMessage(config.id_adrian, u'Bot reiniciado')

# avisa o roger que o bot foi iniciado no servidor
bot.sendMessage(config.id_roger, mensagem.bot_boot)

# loop infinito somente para o arquivo .py não parar aqui
while 1:
   
   # se existe um novo membro, espera 30s para kickar caso ele não responda o captcha corretamente
   if (DadosNovoMembro['memberid'] > 1):
      print 'contagem regressiva para kick'
      time.sleep(30)
      if (DadosNovoMembro['memberid'] > 0):
         bot.kickChatMember(DadosNovoMembro['chatid'], DadosNovoMembro['memberid'])
         DadosNovoMembro['memberid'] = 0
         DadosNovoMembro['chatid'] = 0
