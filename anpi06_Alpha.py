# -*- coding: utf-8 -*-

"""
anpi06_Alpha.py

安否確認メールが kawajun に届くと、
cometsum　に転送される。

anpi01　が、定期的にcometsum を確認し、
安否確認メールを見つけたら、LINEにメッセージを送信する。
一度LINEに送信したらなんども送信しないように
cometsumに安否リセットをグーグルアカウントから送信する。

2019/11/20　基本動作
2019/11/21　
    本プログラムは安否メールを監視し、LINEに転送するもので、
    失敗すると良くないので、最大３つのプログラム（エージェント）
    が、交互にどうさするようにして、２つのエージェントが落ちても
    サービスを止めないようにする。またエージェントの監視をし
    問題があれば、管理者に通知する。
    エージェントは最大３台
    エージェントID
    ID:1 アルファ　alpha　ID:2 ベータ　beta　ID:3 ガンマ　gamma
    として、エージェントの数に関わらず、１０分周期でメール監視を行う。
    エージェント監視の結果　エージェント数　agent_n で制御行う。

2019/11/22
    ヘルスチェック機能追加
    通信出来ないときは、落ちずに、回復するまで処理を続ける。
    安否転送緊急停止　機能追加
2019/11/27
    agent認識を追加、agent同期昨日を追加、
2019/11/28
    5分周期対応
2019/12/1
    メールチェックでエラーがあると、flag=1で返していたのを修正
2019/12/4
    04　構成制御が発生した場合、メール通知する。
2019/12/5
    05  cometsumに送った、「安否確認システム」はテストメッセージにする。
        「安否確認転送システムテスト」　がその文言。
2019/12/12
    06  cometsumメールを確認してから、リセットメール送るまでの間に
        安否メールが来た場合見逃してしまう。これを見逃さないにはどうするか？
        1.新たなメールが来ていないことを確認して、直ぐにリセットを送る。
        　見逃す確率は少なくなるが、0にはならない
          *メール送信するのに3秒かかるので、対策としては不適
        2.リセットを2つ確認する
        　確率は更に少なくなるが、0にはならないが極小となる
        　二度通知する、ゴミが多いと取りこぼす
        対策2.を実施する。
2020/03/02
    07  エージェント不在が2回以上続いたら警報
        ただし、構成制御は1回で実施する。
        ログ記録追加
        ・復帰時1回で警報しちゃうを改修
        ・色々ログ
        ・定時ログ
        　
"""
import subprocess
# ----------------------- 最初に　エージェント設定 ---------------------------
agent = 'Alpha'      # エージェント名　Alpha or Beta
agent_n = 2          # 1台運用　or 2台運用
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

# メールアドレス設定
alarm_address = 'nobu'    # 管理者へのメール
check_address = 'comet'   # 安否メール

import time
import datetime
from anpi_LIB import Lib_LINE
from anpi_LIB import Lib_Mail
from anpi_LIB import agent_check

###################log print#####################
# 自身のプログラム名からログファイル名を作る
import sys
args = sys.argv
logFileName = args[0].strip(".py") + "_log.csv"
# ログファイルにプログラム起動時間を記録
import csv
# 日本語文字化けするので、Shift_jisやめてみた。
f = open(logFileName, 'a')
csvWriter = csv.writer(f)
csvWriter.writerow([datetime.datetime.now(),'  program start!!'])
f.close()
#----------------------------------------------
def log_print(msg1="",msg2="",msg3=""):
    # エラーメッセージなどをプリントする際に、ログファイルも作る
    # ３つまでのデータに対応
    print(msg1,msg2,msg3)
    # f = open(logFileName, 'a',encoding="Shift_jis") 
    # 日本語文字化けするので、Shift_jisやめてみた。
    f = open(logFileName, 'a')
    csvWriter = csv.writer(f)
    csvWriter.writerow([datetime.datetime.now(),msg1,msg2,msg3])
    f.close()
################################################

def speakPrint(say_word):
    print(say_word)
    try:
        subprocess.run('~/julius/jsay_mei.sh ' + say_word,shell=True)
    except:
        print('jsayエラーが発生しました。')
    return

def main():
    # プログラム起動　報告
    Lib_LINE.Line_sendMessage('安否確認転送　起動しました。'  + agent,' token_kakunin')
    # 安否確認メールの確認をするタイミングを設定
    anpi_check_time = [1,6,16,21,26,31,36,41,46,51,56] #おかしい時 の周期
    if agent == 'Alpha':
        if agent_n == 1:
            anpi_check_time = [0,5,10,15,20,25,30,35,40,45,50,55] #エージェント数 1 の周期
        if agent_n == 2:
            anpi_check_time = [ 0,10,20,30,40,50] #エージェント数 2 の周期
    elif agent == 'Beta':
            anpi_check_time = [5,15,25,35,45,55] #エージェント数 2 の周期

    agent_check_time = [3,13,23,33,43,53]  #エージェントの存在確認周期
    agent_sync_time = [2,12,22,32,42,52]   #エージェントの存在確認の前にタイミングを合わせる

    mail_n = 7 # 取得するメールの数
    chkString_1 = "安否確認転送システムテスト"   # テストメッセージ
    chkString_2 = "安否リセット"                 # 通常状態
    chkString_3 = "安否転送ヘルスチェック"       # ヘルスチェック
    chkString_4 = "安否転送緊急停止"             # これを受けると転送処理が止まる
    # 緊急停止メールを送ると、全てのagentが同時に止まるわけではないが、
    # 転送通知はおこなわなくなり、そのうち停止する。

    agent_n_tmp = agent_n # 一時的運用台数
    agent_n_change = 0    # エージェント台数が変化、構成制御発生

    log_count = 0 # 定時ログを一回だけ記録

    while True:
        
        dt_now = datetime.datetime.now()
        time_now = str(dt_now.hour) + "時" + str(dt_now.minute) +  "分 " 
        print('status ',time_now,agent,agent_n,anpi_check_time)

        # 他のエージェントの存在確認、構成制御
        if agent_n == 2:
            if dt_now.minute in agent_check_time:
                result = agent_check.agent_check(agent,udp_set)
                # 誰もいない場合
                if result == 'no':
                    log_print('誰もいなかったので、一人で続けます。',agent)
                    anpi_check_time = [0,5,10,15,20,25,30,35,40,45,50,55]
                    # 構成制御が発生したか確認する。
                    if agent_n_tmp == 2:
                        # 構成制御発生
                        agent_n_tmp = 1
                        agent_n_change = 1
                    else:
                        # エージェントが不在継続
                        agent_n_change = agent_n_change + 1
                        log_print('エージェントが不在継続',agent,agent_n_change)
                        # 構成制御が2回発生していれば、メッセージを出力
                        if agent_n_change == 2:
                            log_print('構成制御が発生しました。',agent)
                            sendmail = alarm_address
                            Lib_Mail.sendMail(sendmail,'安否確認転送システムにおいて、構成制御が発生しました。 ' + agent)
                            Lib_LINE.Line_sendMessage('安否確認転送システムにおいて、構成制御が発生しました 確認用'  + agent,' token_kakunin')
                # 相手かいる場合
                else:
                    # 構成制御が発生したか確認する。
                    if agent_n_tmp == 1:
                        log_print(result,'さんがいました。')
                        # 構成制御発生
                        if agent == 'Alpha':
                            anpi_check_time = [ 0,10,20,30,40,50]  #エージェント数 2 の周期
                        if agent == 'Beta':
                            anpi_check_time = [5,15,25,35,45,55] #エージェント数 2 の周期
                        if agent_n_change > 1:
                            log_print('エージェントが復活',agent,agent_n_change)
                            sendmail = alarm_address
                            Lib_Mail.sendMail(sendmail,'安否確認転送システムにおいて、復活 構成制御が発生しました。 ' + agent)
                            Lib_LINE.Line_sendMessage('安否確認転送システムにおいて、復活 構成制御が発生しました 確認用'  + agent,' token_kakunin')
                        agent_n_tmp = 2
                        agent_n_change = 0
                    else:
                        # 構成制御発生せず
                        agent_n_change = 0


        if dt_now.minute in anpi_check_time:
            # cometsum のメールを確認する。
            flag = Lib_Mail.rcvMail(mail_n,chkString_1,chkString_2,chkString_3,chkString_4)
            print('mail_flag= ',flag)
            
            # "安否リセットなら 重ねて安否リセットを送信" 
            if flag == 2:
                sendmail = check_address
                Lib_Mail.sendMail(sendmail,'安否リセット 2' + agent)

            # "安否確認が来ていたら、通知を行ったのちに安否リセットを送信
            if flag == 1:
                # 20秒後にもう一度、メールチェックする。
                time.sleep(20)
                flag = Lib_Mail.rcvMail(mail_n,chkString_1,chkString_2,chkString_3,chkString_4)
                print('secndoCheck mail_flag= ',flag)
                if flag == 1:
                    result = Lib_LINE.Line_sendMessage('安否確認来たよ!!  G  ************　ただし、誤報の場合もあるので、そこのところ、よろしく。1 ' + agent,'token_G')
                    time.sleep(10)
                    if result == 'LINE Erorr':
                        result = Lib_LINE.Line_sendMessage('安否確認来たよ!!  G  ************　ただし、誤報の場合もあるので、そこのところ、よろしく。2 ' + agent,'token_G')
                        sendmail = alarm_address
                        Lib_Mail.sendMail(sendmail,'LINE G に安否転送を送れませんでした。　' + agent)
                        log_print('LINE G に安否転送を送れませんでした。 ',agent)
                    Lib_LINE.Line_sendMessage('安否確認来たよ!!  11 確認用 ' + agent,' token_kakunin')
                    sendmail = check_address
                    if result != 'LINE Erorr':
                        Lib_Mail.sendMail(sendmail,'安否リセット 11 ' + agent)
                    speakPrint('安否確認メールが来ました。メールを確認してください。')
                else:
                    Lib_LINE.Line_sendMessage('一旦 1を検出したが、次は違うかった何かおかしい。  10 確認用'  + agent,' token_kakunin')
                    sendmail = alarm_address
                    Lib_Mail.sendMail(sendmail,'一旦 1を検出したが、次は違うかった何かおかしい。  10 ' + agent)
                    log_print('一旦 1を検出したが、次は違うかった何かおかしい。  10 ',agent)

            #　安否関係のメールが無かった　少なくともリセットメールを見つけないとダメ
            if flag == 0:
                Lib_LINE.Line_sendMessage('異常処理 確認もリセットも無し、or mail erorr。  0 確認用'  + agent,' token_kakunin')
                #　この状態なら何らかの処置が必要なので、管理者に通知する。
                #　メールで管理者に通知
                sendmail = alarm_address
                # Lib_Mail.sendMail(sendmail,'異常処理 確認もリセットも無し、or mail erorr。  0 ' + agent)
                log_print('異常処理 確認もリセットも無し、or mail erorr。  0 ',agent)

            #　安否関係のメールが無かった　少なくともリセットメールを見つけないとダメ
            if flag == 3:
                Lib_LINE.Line_sendMessage('安否転送ヘルスチェックを受信  3 確認用 ' + agent,' token_kakunin')
                #　この状態なら何らかの処置が必要なので、管理者に通知する。
                #　メールで管理者に通知
                sendmail = alarm_address
                Lib_Mail.sendMail(sendmail,'安否転送ヘルスチェックを受信しました。 3 ' + agent)
                log_print('安否転送ヘルスチェックを受信しました。 3  ',agent)
                sendmail = check_address
                Lib_Mail.sendMail(sendmail,'安否リセット 3 ' + agent + ' ') 

            #　安否転送緊急停止
            if flag == 4:
                Lib_LINE.Line_sendMessage('安否転送緊急停止。  確認用'  + agent,' token_kakunin')
                sendmail = alarm_address
                Lib_Mail.sendMail(sendmail,'安否転送緊急停止。' + agent)
                log_print('安否転送緊急停止。 ',agent)
                raise ValueError("安否転送緊急停止!!")

            #　安否確認転送システムテスト
            if flag == 5:
                Lib_LINE.Line_sendMessage('テストメッセージ　安否確認転送　5' + agent,'token_G')
                Lib_LINE.Line_sendMessage('テストメッセージ　安否確認転送　5 確認用'  + agent,' token_kakunin')
                sendmail = alarm_address
                Lib_Mail.sendMail(sendmail,'テストメッセージ　安否確認転送。 5' + agent)
                log_print('テストメッセージ　安否確認転送。 5  ',agent)
                sendmail = check_address
                Lib_Mail.sendMail(sendmail,'安否リセット 5 ' + agent + ' ') 

            time.sleep(55)
        time.sleep(50)

        # 定時ログ記録
        if dt_now.hour in [6]:
            if dt_now.minute in [4]:
                if  log_count == 0:
                    log_print('定時ログ記録　6:04 ',agent,log_count)
                    log_count = 1
            if dt_now.minute in [14]:
                    log_count = 0

        # エージェント同士を同期させる。
        dt_now = datetime.datetime.now()
        while dt_now.minute in agent_sync_time:
            dt_now = datetime.datetime.now()
            print(dt_now.second,end='', flush=True)
            if   dt_now.second > 50 :time.sleep(0.1)
            elif dt_now.second > 40 :time.sleep(0.5)
            elif dt_now.second > 20 :time.sleep(3)
            else                    :time.sleep(5)


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        log_print("key入力がありましたので、プログラム停止" )
    except ValueError as e:
        log_print(e)
