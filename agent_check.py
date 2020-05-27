# -*- coding: utf-8 -*-
"""
エージェント間のヘルスチェック用のプログラム
UDPを使って通信しています。

UDP　ブロードキャスト通信　
サーバー
agent_check.py

2019/11/20
2019/11/26 anpi用に調整
2019/11/27 Lib化  関数外で設定していたものは　mainルーチンで設定する。
        　　なので、このLIB単独では動作しません。
2020/05/22  Gammarが良くエージェントがいないと言っているのは
            udp_receveが一回しかチェックしていなかったからでした。

"""

def udp_send(msg,udp_set):
    import socket
    import time
    # 1つのメッセージを2秒毎に6回送信、最後に「end」を送る。計7個
    print('step-2',msg,udp_set)
    agent_s_bind = udp_set[0]
    agent_s_adrr = udp_set[1]
    agent_c_bind = udp_set[2] 
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.settimeout(0.2)
    server.bind(("", agent_s_bind))
    try:
        send_mes = ''
        #print('step-21',agent_s_bind,agent_s_adrr,agent_c_bind)
        for i in range(6):
            msg_ = msg + '-' + str(i)
            message = msg_.replace('b', '').encode('utf-8')
            #print('step-22')
            server.sendto(message, ('<broadcast>', agent_s_adrr))
            print("message sent!",i,msg)
            send_mes = send_mes + ' ' + msg_
            time.sleep(2)
        #print('step-23')
        msg_ =  'end'
        send_mes = send_mes + ' ' + msg_
        message = msg_.replace('b', '').encode('utf-8')
        server.sendto(message, ('<broadcast>', agent_s_adrr))
        #print('step-24')
    except:
        print('送信エラー')
        send_mes = send_mes + ' ' + 'send_error'
    finally:
        return send_mes

def udp_receve_sub(udp_set):
    import socket
    import time
    agent_s_bind = udp_set[0]
    agent_s_adrr = udp_set[1]
    agent_c_bind = udp_set[2]
    #print('step-4',agent_s_bind,agent_s_adrr,agent_c_bind)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(('', agent_c_bind))
    client.settimeout(5)
    # 一回受信
    try:
        data, addr = client.recvfrom(20)
        #print('received message: %s'%data)
        return data
    except:
        print('receve_error')
        return b'error'

def udp_receve(udp_set):
    # 最初は取り逃しても最後まで受ける　endを含め最大7個
    rcv_mess = b''
    for i in range(7):
        # print(i+1,'回目のチェック',udp_set)
        data = udp_receve_sub(udp_set)
        #print('receve=' ,data)
        rcv_mess = rcv_mess + b' ' + data
        print('rcv_mess=' ,rcv_mess)
        if rcv_mess == 'Alpha' or rcv_mess == 'Beta' :
            break
    return rcv_mess

def agent_check(agent,udp_set):
    print()
    print(agent,'エージェント生存確認をします。')
    print('step-5',udp_set)
    if agent == 'Alpha':
        # 送信
        print('step-01',agent,udp_set)
        send_mess = udp_send(agent,udp_set)
        print(send_mess)
        if agent in send_mess:
            #print(agent)
            pass
        else:
            print('no')
        # 受信
        rcv_mess = udp_receve(udp_set)
        print(rcv_mess)
        rcv_mess = rcv_mess.decode('sjis')
        print()
        if 'Beta' in rcv_mess:
            #print('Beta')
            return 'Beta'
        else:
            print('no')
            return 'no'

    if agent == 'Beta':
        # 受信
        rcv_mess = udp_receve(udp_set)
        print(rcv_mess)
        rcv_mess = rcv_mess.decode('sjis')
        if 'Alpha' in rcv_mess:
            #print('Alpha')
            result = 'Alpha'
        else:
            #print('no')
            result = 'no'
        # 送信
        send_mess = udp_send(agent,udp_set)
        print(send_mess)
        if agent in send_mess:
            #print(agent)
            pass
        else:
            print('no')
        return result

def agent_check_Gamma(agent,udp_set):
    # Gamma専用のエージェントチェック
    print()
    print(agent,'エージェント生存確認をします。')

    # アルファさんの生存確認
    udp_set[2] = 37021
    rcv_mess = udp_receve(udp_set)
    print(rcv_mess)
    rcv_mess = rcv_mess.decode('sjis')
    if 'Alpha' in rcv_mess:
        print('Alpha')
        result = 'Alpha'
    else:
        #print('no')
        result = ''

    # ベータさんの生存確認
    udp_set[2] = 37022
    rcv_mess = udp_receve(udp_set)
    print(rcv_mess)
    rcv_mess = rcv_mess.decode('sjis')
    if 'Beta' in rcv_mess:
        print('Beta')
        result = result + ' Beta'
    else:
        print('no')
        result =  result + ''

    if result == '' : result = 'no'
    return result

def main():

    #　Gamma 用のテストプログラム

    # ----------------------- 最初に　エージェント設定 ---------------------------
    agent = 'Gamma'      # エージェント名　Alpha or Beta
    agent_n = 1          # 1台運用　or 2台運用
    # ----------------------- 最初に　UDP 設定 ---------------------------------
    if agent == 'Alpha':
        agent_s_bind = 44444
        agent_s_adrr = 37021
        agent_c_bind = 37022
    else:
        agent_s_bind = 44443
        agent_s_adrr = 37022
        agent_c_bind = 37021  
    udp_set = [agent_s_bind,agent_s_adrr,agent_c_bind]
    #-------------------------------------------------------------------------

    result = agent_check_Gamma(agent,udp_set)

    print(result,'--が戻り値でした。')

    """ helthcheck　の戻り値
        'Alpha' 'Beta'  別のエージェントがいた場合　自分と違うエージェント名が返って来るはず 
        'no'　　　　　　　他のエージェントがいなかった場合
    """

if __name__ == '__main__':
    try:
        main()
    #when 'Ctrl+C' is pressed,child program destroy() will be executed.
    except KeyboardInterrupt:
        print('Ctrl+C key input')
