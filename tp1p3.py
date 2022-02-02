import threading
import numpy as np
import math
import matplotlib.pyplot as plt
import time
import asyncio
import multiprocessing
import socket
from simple_pid import PID

#Vetores
listAlt1 = []; listAlt2 = []; listAct1 = []; listAct2 = []

#Variaveis dos tanques 
r1Min = 1; r2Min = 1; r1Max = 3; r2Max = 2
h1Max = 5; h2Max = 3.5
alt1 = 0; alt2 = 0
exit1 = 0; exit2 = 0
coef1 = 0.4; coef2 = 0.35


#Variaveis gerais
dt = 0.1 #Período da Simulação de 100ms como sugere a especificação
act1 = 0 # Atuador nº1
act2 = 0 # Atuador nº2
setP1 = h1Max*0.6; setP2 = h2Max*0.6
setP1Din = 0; setP2Din = 0
tot = 0.02

#Mutex para os processos
listAlt1_mutex = threading.Lock()
listAlt2_mutex = threading.Lock()
listAct1_mutex = threading.Lock()
listAct2_mutex = threading.Lock()
alt1_mutex = threading.Lock()
alt2_mutex = threading.Lock()
setP1_mutex = threading.Lock()
setP2_mutex = threading.Lock()
act1_mutex = threading.Lock()
act2_mutex = threading.Lock()

def conect (cliente, endereco):
    pass


#Integração númerica como sugerido na especificação
def integ(act1,act2, exit0, raioMin, raioMax, alt, altMax, temp):
    alt = (((act1 - exit0 - act2)/(3.14*(raioMin+(((raioMax-raioMin)/altMax)*alt)))**2)*temp)

    return alt

def interface():
    global setP1, setP2, setP1Din, setP2Din
    while (setP1Din == 0 or setP2Din == 0):
        try:
            print("\nSe deseja alterar o setpoint do tanque 1, digite o valor e tecle enter\n")
            print("\nSe não digite 0 e tecle enter\n" )
            print("\nO programa continua rodando e você pode acompanhar pelo arquivo log.txt\n")
            setP1Din = input("--> ")
        except ValueError:
            print("Invalid number")    
        if (int(setP1Din) != 0):
            setP1_mutex.acquire()
            setP1 = int(setP1Din)
            setP1_mutex.release()
            print("\n \n \n \n \n *******************************VALOR DIGITADO PARA O SETPOINT 1*********************\n \n \n \n \n ")
            print(setP1Din)
            print("\n \n \n \n \n")
            print("***********************************************************************************")
            setP1Din = 0
        else :
            print("O valor do tanque 1 continuou como no inicio")
            print("\nO programa continua rodando e você pode acompanhar pelo arquivo log.txt\n")
        try:
            print("\nSe deseja alterar o setpoint do tanque 2, digite o valor e tecle enter\n")
            print("\nSe não digite 0 e tecle enter\n" )
            print("\nO programa continua rodando e você pode acompanhar pelo arquivo log.txt\n")
            setP2Din = input("--> ")
        except ValueError:
            print("\nInvalid number") 
        if (int(setP2Din) != 0):
            setP2_mutex.acquire()
            setP2 = int(setP2Din)
            setP2_mutex.release()
            print("\n \n \n \n \n *******************************VALOR DIGITADO PARA O SETPOINT 2*********************\n \n \n \n \n ")
            print(setP2Din)
            print("\n \n \n \n \n")
            print("***********************************************************************************")
            setP2Din = 0
        else :
            print("\nO valor do tanque 2 continuou como no inicio\n")
            print("\nO programa continua rodando e você pode acompanhar pelo arquivo log.txt\n")

#Função que representa o funcionamento do 1º tanque
def tan1(coef,raioMin,raioMax,hMax):
    global alt1, setP1, setP2, listAlt1, act1,act2, dt, exit1, setP1Din, setP2Din
    time.sleep(2)
    while(alt1 < setP1-tot and alt2 < setP2-tot):
        #Diretiva de proteção do SO
        listAlt1_mutex.acquire()
        listAlt1.append(alt1)
        listAlt1_mutex.release()
        #Saída dos tanques como demonstrado na especificação
        exit1 = coef*math.sqrt(alt1)
        alt1_mutex.acquire()
        alt1 = integ(act1,act2,exit1,raioMin,raioMax,alt1,hMax,dt) + alt1
        alt1_mutex.release()
        if alt1 >= hMax:
            alt1_mutex.acquire()
            alt1 = hMax
            alt1_mutex.release()
        time.sleep(dt)
    print("A Thread do Tanque nº 1 finalizou")

#Função que representa o funcionamento do 2º tanque
def tan2(coef,raioMin,raioMax,hMax):
    global setP1,setP2,act2,listAlt2, alt1,alt2, dt, exit2, setP1Din, setP2Din
    time.sleep(2)
    while(alt1 < setP1-tot and alt2 < setP2-tot): 
        #Diretiva de proteção do SO
        listAlt2_mutex.acquire()
        listAlt2.append(alt2)
        listAlt2_mutex.release()
         #Saída dos tanques como demonstrado na especificação
        exit2 = coef*math.sqrt(alt2)
        alt2_mutex.acquire()
        alt2 = integ(act2,0, exit2, raioMin, raioMax,alt1,hMax, dt) + alt2
        alt2_mutex.release()        
        if alt2 >= hMax:
            alt2_mutex.acquire()
            alt2 = hMax
            alt2_mutex.release()
        time.sleep(dt)
    print("A Thread do Tanque nº 2 finalizou")  

#Thread Referente ao Controlador
def controlador(): 
    global h1Max,setP1,setP2,act1,act2,alt1,alt2,setP1Din, setP2Din,exit1,exit2
    time.sleep(2)

    #Controle padrão recomendado pelos desenvolvedores da biblioteca PID
    control1 = PID(1,0.1,0.05, setpoint = setP1)
    control2 = PID(1,0.1,0.05, setpoint = setP2)
    #Loop que vai faz com que o controlador faça suas operações enquanto o valor da altura não estiver perto do setpoint, a variável tot é a tolerância
    while(alt1 < setP1-tot and alt2 < setP2-tot):
        listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen.connect( ('127.0.0.1', 5032))       
        output0 = str(alt1)
        output1 = str(alt2)
        output2 = str(exit1)
        output3 = str(exit2)
        output4 = str(' A altura do tanque 1 e: ' + output0 + ' | A altura do tanque 2 e: ' + output1 + '\nA vazao do tanque 1 e: ' + output2+ ' | A vazao do tanque 2 e: ' + output3).encode('utf-8')
        listen.send(output4)
        data = listen.recv(1024)
        listen.close()
        if not data:
            exit
        print("Received\n")
        repr(data)

        listAct1_mutex.acquire()
        listAct1.append(act1)
        listAct1_mutex.release()
        listAct2_mutex.acquire()
        listAct2.append(act2)
        listAct2_mutex.release()        
        #Verificação da tolerância e mudança no valor da vazão do tanque º1
        if(alt1 < setP1-tot):
            act1_mutex.acquire()            
            act1 = control1(alt1)
            act1_mutex.release()
        #Verificação da tolerância e mudança no valor da vazão do tanque º2
        if(alt2 < setP2-tot):
            act2_mutex.acquire()
            act2 = control2(alt2)
            act2_mutex.release()
        # Fazendo com que a thread do PLC seja executada na metade da frequência como manda a especificação
        time.sleep(dt*2)
    print("O Controle foi realizado!")


async def logger():
    global alt1, alt2, exit1, exit2
    fid = open('log.txt','w')
    fid.write('Alturas e saidas\n')
    while(alt1 <= setP1-tot and alt2 <= setP2-tot):
        aux = time.gmtime(time.time() - inicio)
        auxResult = time.strftime("%H:%M:%S",aux)
        fid = open('log.txt','a+')
        fid.write('Tempo de exucacao= ' + str(auxResult) +' | ' +' altura 1= ' + str(alt1) +' | '+ ' altura 2= ' + str(alt2) +' | '+ ' saida 1= ' + str(exit1) +' | '+ ' saida 2= ' + str(exit2) +' | '+'\n')
        await asyncio.sleep(1)
    fid.close()

def synopitc():  

    #Listen
    listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen.bind( ('127.0.0.1', 5032))
    listen.listen ( 0 )
    print('\nEsperando o Cliente \n')
    fid = open('historiador.txt','w')
    fid.write('Alturas e saidas\n')
    while True:
        cliente, endereco = listen.accept()
        data = cliente.recv(1024)
        print('\nO cliente  é: \n')
        print(endereco)
        print('\nO dado  é: \n')
        x = data.decode('utf-8')
        print(x)        
        aux = time.gmtime(time.time() - inicio)
        auxResult = time.strftime("%H:%M:%S",aux)
        fid = open('historiador.txt','a+')
        fid.write('No Tempo de execucacao= ' + str(auxResult) +' | ' + x + '\n\n')
        time.sleep(1)        
        if not x:
            exit
        cliente.sendall(data)
    cliente.close()
    print("O processo do Sinoptico finalizou")  


if __name__ == '__main__':   
    #Criando as threads
    print("Simulação de um controle de 2 tanques de água")
    inicio = time.time()
    interface_thread = threading.Thread(target = interface,name = 'Interface')
    process_thread_1 = threading.Thread(target = tan1,name = 'Tanque nº 1',args=(coef1,r1Min,r1Max,h1Max))
    process_thread_2 = threading.Thread(target = tan2,name = 'Tanque nº 2',args=(coef2,r2Min,r2Max,h2Max))
    softPLC_thread = threading.Thread(target = controlador,name = 'Controlador')
    logger_thread = threading.Thread(target = logger,name = 'Logger')
    synopitc_process = multiprocessing.Process(target = synopitc,name= 'Synopitc')

    interface_thread.start()
    process_thread_1.start()
    process_thread_2.start()
    synopitc_process.start()
    softPLC_thread.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(logger())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    threads = []
    threads.append(process_thread_1)
    threads.append(process_thread_2)
    threads.append(softPLC_thread)

    for t in threads:
        t.join()
    totalTime = time.gmtime(time.time() - inicio)
    result = time.strftime("%H:%M:%S",totalTime)

    print("FIMMMM...")
    print (result, " Foi o tempo que o programa gastou para ser executado")

    #Parte do código que plota os gráficos
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)

    po1 = np.arange(0,len(listAlt1),1)/15
    ax1.set_title('Altura do Tanque 1 (m)')
    ax1.plot(po1, listAlt1, 'bs'); ax1.grid()
    ax1.axhline(setP1, linewidth=0.8,color='y')

    po2 = np.arange(0,len(listAlt2),1)/15
    ax2.set_title('Altura do Tanque 2 (m)')
    ax2.plot(po2, listAlt2, 'g^'); ax2.grid()
    ax2.axhline(setP2, linewidth=0.8,color='y')

    po3 = np.arange(0,len(listAct1),1)/15
    ax3.set_title('Nível Controlador 1')
    ax3.plot(po3, listAct1, 'r--'); ax3.grid()

    po4 = np.arange(0,len(listAct2),1)/15
    ax4.set_title('Nível Controlador 2')
    ax4.plot(po4, listAct2, 'r--'); ax4.grid()

    plt.show()