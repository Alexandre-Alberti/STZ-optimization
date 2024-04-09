#import math
import numpy as np
from numpy import random as rd
import pandas as pd
from scipy.integrate import quad, dblquad
from scipy.optimize import minimize
import streamlit as st

# Funções e definições anteriores

def main():
    col1, col2, col3 = st.columns(3)

    st.image("RANDOM.png")
    #foto = Image.open('RANDOM.png')
    #col2.image(foto, use_column_width=True)

    st.title('Política STZ - uma política flexível de substituição por idade')

    menu = ["Aplicação", "Informação", "Website"]
    choice = st.sidebar.selectbox("Selecione aqui", menu)
    
    if choice == menu[0]:
        st.header(menu[0])
        st.subheader("Insira os valores dos parâmetros abaixo:")
        
        beta = st.number_input('Beta - parâmetro de forma da distribuição de probabilídade de Weibull para o tempo até a falha',format="%.7f", step = 0.0000001)
        eta = st.number_input('Eta - parâmetro de escala da distribuição de probabilídade de Weibull para o tempo até a falha', format="%.7f", step = 0.0000001)    
        lbda = st.number_input('Lambda - taxa de chegada de oportunidades para manutenção', format="%.7f", step = 0.0000001)
        cp = st.number_input('Cp - custo de substituição preventiva em T (programada)', format="%.7f", step = 0.0000001) 
        cv = st.number_input('Cv - custo de substituição preventiva em Z (prorrogada)', format="%.7f", step = 0.0000001)
        co = st.number_input('Co - custo de substituição preventiva antecipada por oportunidade', format="%.7f", step = 0.0000001) 
        cw = st.number_input('Cw - custo de substituição preventiva em oportunidade posterior a T', format="%.7f", step = 0.0000001)
        cf = st.number_input('Cf - custo de substituição corretiva', format="%.7f", step = 0.0000001) 
        p = st.number_input('P - probabilidade de impedimento para substituição preventiva na data programada', format="%.7f", step = 0.0000001)
        
        st.subheader("Clique no botão abaixo para rodar esse aplicativo:")
        
        botao = st.button("Obtenha os valores")
        if botao: 
            resultados = [] 
            # Definições das funções
            def fx(x): 
                f = (beta/eta)*((x/eta)**(beta-1))*np.exp(-(x/eta)**beta) 
                return f 
            def Fx(x):
                return 1 - np.exp(-(x/eta)**beta) 
            def Rx(x): 
                return 1 - Fx(x)
                    
            def fh(h):
                return lbda*np.exp(-(lbda*h))
            def Fh(h):
                return 1 - np.exp(-(lbda*h)) 
            def Rh(h): 
                return 1- Fh(h) 

            def objetivo(y):
    
                S=y[0]
                T=y[1]
                Z=y[2]
    
                #CASO 1
                def P1(S):
                    return Fx(S)
                def C1(S):
                    return cf*P1(S)
                def V1(S):
                    return (quad(lambda x: x*fx(x), 0, S)[0])  
    
                #CASO 2
                def P2(S,T):
                    return Rh(T-S)*(Fx(T) - Fx(S)) + (dblquad(lambda x, h: fh(h)*fx(x), 0, T-S, lambda h: S, lambda h: S+h)[0])
                def C2(S,T):
                    return cf*P2(S,T)
                def V2(S,T):
                    return Rh(T-S)*(quad(lambda x: x*fx(x), S, T)[0])+ (dblquad(lambda x, h: x*fh(h)*fx(x), 0, T-S, lambda h: S, lambda h: S+h)[0])
                
                #CASO 3
                def P3(S,T,Z):
                    return p*Rh(Z-S)*(Fx(Z)-Fx(T)) + p*(dblquad(lambda x, h: fh(h)*fx(x), T-S, Z-S, lambda h: T, lambda h: h+S)[0])
                def C3(S,T,Z):
                    return cf*P3(S,T,Z)
                def V3(S,T,Z):
                    return  p*Rh(T-S)*(quad(lambda x: x*fx(x), T, Z)[0]) + p*(dblquad(lambda x, h: x*fh(h)*fx(x), T-S, Z-S, lambda h: T, lambda h: h+S)[0])
                
                #CASO 4
                def P4(S,T):
                    return (quad(lambda h: fh(h)*Rx(S+h), 0, T-S)[0])
                def C4(S,T):
                    return co*P4(S, T)
                def V4(S,T):
                    return (quad(lambda h: (S+h)*fh(h)*Rx(S+h), 0, T-S)[0])
    
                #CASO 5
                def P5(S,T,Z):
                    return p*(quad(lambda h: fh(h)*Rx(S+h), T-S, Z-S)[0])
                def C5(S,T,Z):
                    return cw*P5(S, T, Z)
                def V5(S,T,Z): 
                    return p*(quad(lambda h: (S+h)*fh(h)*Rx(S+h), T-S, Z-S)[0])
    
                #CASO 6
                def P6(S,T):
                    return (1-p)*Rh(T-S)*Rx(T) 
                def C6(S,T):
                    return cp*P6(S, T)
                def V6(S,T):
                    return T*P6(S, T)
    
                #CASO 7 
                def P7(S,T,Z):
                    return p*Rh(Z-S)*Rx(Z)
                def C7(S,T,Z):
                    return cv*P7(S, T, Z)
                def V7(S,T,Z):
                    return Z*P7(S, T, Z)
    
                SOMA_PROB=P1(S)+P2(S,T)+P3(S, T, Z)+P4(S, T) + P5(S, T, Z) + P6(S, T)+P7(S, T, Z)
                SOMA_CUST=C1(S)+C2(S,T)+C3(S, T, Z)+C4(S, T) + C5(S, T, Z) + C6(S, T)+C7(S, T, Z)
                SOMA_VIDA=V1(S)+V2(S,T)+V3(S, T, Z)+V4(S, T) + V5(S, T, Z) + V6(S, T)+V7(S, T, Z)
    
                PROB_FALHA = P1(S)+P2(S,T)+P3(S, T, Z)
                
                TAXA_CUSTO=SOMA_CUST/SOMA_VIDA
                MTBOF=SOMA_VIDA/PROB_FALHA
    
                return TAXA_CUSTO, MTBOF, SOMA_PROB

            # Otimização por meta-heurísticas
            # Começo por algoritmo genético
            
            populacao = 500
            evolucoes = 5
            
            # gerando a populacao inicial 
            num_linhas = populacao
            num_colunas = 4
            
            geracao_1 = [[0] * num_colunas for _ in range(num_linhas)]
            geracao_2 = geracao_1
            
            #populacao inicial
            
            for i in range(0,populacao):
                Z = rd.uniform(0,10*eta)
                T = rd.uniform(0,Z)
                S = rd.uniform(0,T)
                geracao_1[i][0] = S
                geracao_1[i][1] = T
                geracao_1[i][2] = Z
                geracao_1[i][3] = objetivo([S,T,Z])[0]
            
            geracao_2 = geracao_1
            geracao_ordenada = sorted(geracao_1, key=lambda linha: linha[3])
            print('gen_1',geracao_ordenada[0])
            
            #iteracoes
            for n in range(0,evolucoes):
            
                geracao_ordenada = sorted(geracao_1, key=lambda linha: linha[3])
            
                # 40% dos melhores individuos permanecem
                for i in range(0,int(0.4*populacao)):
                    geracao_1[i] = geracao_ordenada[i]
            
                # 10% de individuos aleatórios permanecem
                for i in range(int(0.4*populacao),int(0.5*populacao)):
                    j = rd.randint(0.4*populacao,populacao)
                    geracao_1[i] = geracao_ordenada[j]
            
                # os demais 50% são obtidos por meio de cruzamentos e mutação
                for i in range(int(0.5*populacao),populacao):
                    j_1 = rd.randint(0,populacao)
                    j_2 = rd.randint(0,populacao)
                    gene_herdado_de_2 = rd.randint(0,3)
                    novo_individuo = geracao_2[j_1]
                    novo_individuo[gene_herdado_de_2] = geracao_2[j_2][gene_herdado_de_2]
                
                    S = novo_individuo[0]
                    T = novo_individuo[1]
                    Z = novo_individuo[2]
                
                    # as mutações vem quando a solução é incompatível com a política
                    if (T > Z):
                        T = rd.uniform(0,Z)
                
                    if (S > T):
                        S = rd.uniform(0,T)
                        
                    fitness_novo = objetivo([S,T,Z])[0]
                
                    novo_individuo = [S,T,Z,fitness_novo] 
                    geracao_1[i] = novo_individuo
                    
                geracao_ordenada = sorted(geracao_1, key=lambda linha: linha[3])    
                geracao_2 = geracao_1
            
            geracao_ordenada = sorted(geracao_1, key=lambda linha: linha[3])
            
            #fazendo busca por meio de uma nuvem de particulas adaptada
            W = 0.1
            C1 = 1.2
            C2 = 1.2
            
            numero_particulas = 50
            movimentos = 5
            
            #formação da nuvem
            # 30 das melhores particulas
            # 20 particulas aleatórias
            
            # gerando a populacao inicial 
            posicoes = [[0] * 1 for _ in range(numero_particulas)]
            melhor_de_cada = [[0] * 1 for _ in range(numero_particulas)]
            velocidades = [[0]*1 for _ in range(numero_particulas)]
            
            for i in range(0,30):
                posicoes[i] = geracao_ordenada[i]
                melhor_de_cada[i] = geracao_ordenada[i]
                velocidades[i] = [0, 0, 0]
            
            for i in range(30,50):
                j = rd.randint(30,populacao)
                posicoes[i] = geracao_ordenada[j]
                melhor_de_cada[i] = geracao_ordenada[j]
                velocidades[i] = [0, 0, 0]
            
            melhor_global = posicoes[0]
            
            #nuvem formada, vou fazer as iterações
            
            for n in range(0,movimentos):
                
                for i in range(0,numero_particulas):
                    r1 = rd.uniform(0,1)
                    r2 = rd.uniform(0,1)
                    velocidade_0 = W*velocidades[i][0] + C1*r1*(melhor_global[0]-posicoes[i][0]) + C2*r2*(melhor_de_cada[i][0]-posicoes[i][0])
                    
                    r1 = rd.uniform(0,1)
                    r2 = rd.uniform(0,1)
                    velocidade_1 = W*velocidades[i][1] + C1*r1*(melhor_global[1]-posicoes[i][1]) + C2*r2*(melhor_de_cada[i][1]-posicoes[i][1])
                    
                    r1 = rd.uniform(0,1)
                    r2 = rd.uniform(0,1)
                    velocidade_2 = W*velocidades[i][2] + C1*r1*(melhor_global[2]-posicoes[i][2]) + C2*r2*(melhor_de_cada[i][2]-posicoes[i][2])
                    
                    velocidades[i] = [velocidade_0, velocidade_1, velocidade_2]
                    
                    S = posicoes[i][0] + velocidades[i][0]
                    T = posicoes[i][1] + velocidades[i][1]
                    Z = posicoes[i][2] + velocidades[i][2]
                    
                    if Z <= 0:
                        Z = rd.uniform(0.2*melhor_global[2], 1.8*melhor_global[2])
                    
                    if (T>Z) or (T<=0):
                        T = rd.uniform(0,Z)
                    
                    if (S>T) or (S<=0):
                        S = rd.uniform(0,T)
                        
                    desempenho_particula = objetivo([S,T,Z])[0]
                    
                    posicoes[i] = [S, T, Z, desempenho_particula]
                    
                    if desempenho_particula < melhor_de_cada[i][3]:
                        melhor_de_cada[i] = posicoes[i]
                    
                    nuvem_ordenada = sorted(melhor_de_cada, key=lambda linha: linha[3])
                    
                melhor_global = nuvem_ordenada[0]
            
            #print(melhor_global)
            S = melhor_global[0]
            T = melhor_global[1]
            Z = melhor_global[2]
            Taxa_de_custo = melhor_global[3]
            MTBOF = objetivo([S,T,Z])[1]
            st.write('S = :', S)
            st.write('T = :', T)
            st.write('Z = :', Z)
            st.write('Taxa de custo = :', Taxa_de_custo)  # Corrigindo o nome da variável
            st.write('Tempo médio entre falhas operacionais = :', MTBOF)  # Corrigindo o nome da variável
            
    if choice == menu[1]:
        st.header(menu[1])
        st.write('''Fazer o texto para colocar aqui''')

    if choice == menu[2]:
        st.header(menu[2])
        st.write('''The Research Group on Risk and Decision Analysis in Operations and Maintenance was created in 2012 
        in order to bring together different researchers who work in the following areas: risk, maintenance and 
        operation modelling. Learn more about it through our website.''')
        st.markdown('[Click here to be redirected to our website](http://random.org.br/en/)', False)

if __name__ == "__main__":
    main()
