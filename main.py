#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# VERSÃO 2.0 DO BOT DE BOAS VINDAS DO GRUPO DO PODCAST VOLT AMPERE NO TELEGRAM #
#-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+#
# AUTOR: ROGER MANRIQUE                                                        #
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
# [P] INTERPRETADOR DE LINGUAGEM NATURAL

# OBS.: FUNÇÃO DE MONTAGEM DE VITRINE PARA O EPISÓDIO TRANSFERIDA PARA OUTRO BOT

import config, mensagem
import telepot, time, feedparser, subprocess, shlex, logging
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telepot.loop import OrderedWebhook

# inicializa token do bot
bot = telepot.Bot(config.token_bot)

# inicializa variável de novo membro para captcha
DadosNovoMembro = {'chatid':0, 'memberid':0}

#flag membro expulso
MembroExpulso = 0

def handle(msg):
   # imprime a mensagem
   print "%s\n" % msg
   
   # pega os dados básicos da mensagem 
   content_type, chat_type, chatid = telepot.glance(msg)
   
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
		 
      # avisa grupo que membro saiu por conta própria
      if MembroExpulso == 0:
         bot.sendMessage(chatid, NomeMembroSaindo + mensagem.tchau)
         
      # avisa que membro foi expulso pelo bot
      else:
         bot.sendMessage(chatid, NomeMembroSaindo + mensagem.expulso)
         MembroExpulso = 0
		 
   ###########################################
   # A PARTIR DESSE PONTO ELE DETECTA TEXTOS #
   ###########################################
   elif content_type == 'text':
      # todas as mensagens são convertida para caracteres minúsculos
      MensagemGrupo = msg['text'].lower()
      
	  # se a flag de novo membro estiver ativa e esse cara respondeu corretamente, zera o timeout para kick
      if (MensagemGrupo.find("4") >= 0 or MensagemGrupo.find("quatro") >= 0) and msg['from']['id'] == DadosNovoMembro['memberid']:
         DadosNovoMembro['memberid'] = 0
         DadosNovoMembro['chatid'] = 0
         bot.sendMessage(chatid, u'Agora sim. ' + mensagem.boasvindas)
      
      # comando /boo
      elif MensagemGrupo == '/boo':
         bot.sendMessage(chatid, mensagem.boo)

      # comando /sai
      elif MensagemGrupo == '/oi':
         bot.sendMessage(chatid, mensagem.saudacao)
	  
# roda o bot como thread em segundo plano
MessageLoop(bot, handle).run_as_thread()

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
         MembroExpulso = 1
