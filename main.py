import math
import numpy as np
import pandas as pd
from scipy.integrate import quad, dblquad
from scipy.optimize import minimize
import streamlit as st
import sys
from streamlit import cli as stcli
from PIL import Image

# Funções e definições anteriores

def main():
    col1, col2, col3 = st.columns(3)
    foto = Image.open('foto.png')
    col2.image(foto, use_column_width=True)

    st.title('Política de Substituição Preventiva com Oportunidade e Prorrogação')

    menu = ["Aplicação", "Informação", "Website"]
    choice = st.sidebar.selectbox("Selecione aqui", menu)
    
    if choice == menu[0]:
        st.header(menu[0])
        st.subheader("Insira os valores dos parâmetros abaixo:")
        
        #beta = st.number_input('Parâmetro de forma (beta)', value=2.0, step=0.1, format='%.1f')
        beta = st.number_input('Parâmetro de forma (beta)')
        eta = st.number_input('Parâmetro de escala (eta)')    
        lbda = st.number_input('Taxa de Chegada de Oportunidade (Lambda)')
        cp = st.number_input('Custo de Substituição Preventiva em T(programado):') 
        cv = st.number_input('Custo de Substituição Preventiva em Z:')
        co = st.number_input('Custo de Substituição Preventiva em Oportunidade:') 
        cf = st.number_input('Custo da manutenção corretiva:') 
        cw = st.number_input('Substituição oportuna entre T e Z:')
        p = st.number_input('#Probabilidade de Impedimento:')
        
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
                S, T, Z = y  # Corrigindo a desestruturação das variáveis
                # CASO 1
                def P1(S):
                    return Fx(S)
                def C1(S):
                    return cf*P1(S)
                def V1(S):
                    return (quad(lambda x: x*fx(x), 0, S)[0])  

                # CASO 2
                def P2(S,T):
                    return Rh(T-S)*(Fx(T) - Fx(S)) + (dblquad(lambda x, h: fh(h)*fx(x), 0, T-S, S, lambda h: S+h)[0])
                def C2(S,T):
                    return cf*P2(S,T)
                def V2(S,T):
                    return Rh(T-S)*(quad(lambda x: x*fx(x), S, T)[0])+ (dblquad(lambda x, h: x*fh(h)*fx(x), 0, T-S, S, lambda h: S+h)[0])

                # CASO 3
                def P3(S,T,Z):
                    return p*Rh(Z-S)*(Fx(Z)-Fx(T)) + p*(dblquad(lambda x, h: fh(h)*fx(x), T-S, Z-S, T, lambda h: h+S)[0])
                def C3(S,T,Z):
                    return cf*P3(S,T,Z)
                def V3(S,T,Z):
                    return  p*Rh(T-S)*(quad(lambda x: x*fx(x), T, Z)[0]) + p*(dblquad(lambda x, h: x*fh(h)*fx(x), T-S, Z-S, T, lambda h: h+S)[0])

                # CASO 4
                def P4(S,T):
                    return (quad(lambda h: fh(h)*Rx(S+h), 0, T-S)[0])
                def C4(S,T):
                    return co*P4(S, T)
                def V4(S,T):
                    return (quad(lambda h: (S+h)*fh(h)*Rx(S+h), 0, T-S)[0])

                # CASO 5
                def P5(S,T,Z):
                    return p*(quad(lambda h: fh(h)*Rx(S+h), T-S, Z-S)[0])
                def C5(S,T,Z):
                    return cw*P5(S, T, Z)
                def V5(S,T,Z): 
                    return p*(quad(lambda h: (S+h)*fh(h)*Rx(S+h), T-S, Z-S)[0])

                # CASO 6
                def P6(S,T):
                    return (1-p)*Rh(T-S)*Rx(T) 
                def C6(S,T):
                    return cp*P6(S, T)
                def V6(S,T):
                    return T*P6(S, T)

                # CASO 7 
                def P7(S,T,Z):
                    return p*Rh(Z-S)*Rx(Z)
                def C7(S,T,Z):
                    return cv*P7(S, T, Z)
                def V7(S,T,Z):
                    return Z*P7(S, T, Z)

                SOMA_PROB=P1(S)+P2(S,T)+P3(S, T, Z)+P4(S, T) + P5(S, T, Z) + P6(S, T)+P7(S, T, Z)
                SOMA_CUST=C1(S)+C2(S,T)+C3(S, T, Z)+C4(S, T) + C5(S, T, Z) + C6(S, T)+C7(S, T, Z)
                SOMA_VIDA=V1(S)+V2(S,T)+V3(S, T, Z)+V4(S, T) + V5(S, T, Z) + V6(S, T)+V7(S, T, Z)

                TAXA_CUSTO=SOMA_CUST/SOMA_VIDA
                return TAXA_CUSTO
            
            x0 = [0.9, 1.0, 2.0]

            def cond1(y):
                return y[1]-y[0] # T >= S

            def cond2(y):
                return y[2]-y[1] # Z >= T

            c1 = {'type': 'ineq', 'fun': cond1}
            c2 = {'type': 'ineq', 'fun': cond2}

            cons = [c1, c2]

            bx0 = [0.1, 50]
            bx1 = [0.1, 50]
            bx2 = [0.1, 50]

            ret = minimize(objetivo, x0, method='SLSQP', bounds=[bx0, bx1, bx2], constraints=cons)
            S, T, Z = ret.x[0], ret.x[1], ret.x[2]

            st.write('S = :', S)
            st.write('T = :', T)
            st.write('Z = :', Z)
            st.write('Taxa de custo = :', ret.fun)  # Corrigindo o nome da variável
            
                # Função MTBOF anterior
            def MTBOF(S,T,Z):
                def P1(S):
                    return Fx(S)
                def C1(S):
                    return cf*P1(S)
                def V1(S):
                    return (quad(lambda x: x*fx(x), 0, S)[0])  
                    
                    #CASO 2
                def P2(S,T):
                    return Rh(T-S)*(Fx(T) - Fx(S)) + (dblquad(lambda x, h: fh(h)*fx(x), 0, T-S, S, lambda h: S+h)[0])
                def C2(S,T):
                    return cf*P2(S,T)
                def V2(S,T):
                    return Rh(T-S)*(quad(lambda x: x*fx(x), S, T)[0])+ (dblquad(lambda x, h: x*fh(h)*fx(x), 0, T-S, S, lambda h: S+h)[0])
                    
                    #CASO 3
                def P3(S,T,Z):
                    return p*Rh(Z-S)*(Fx(Z)-Fx(T)) + p*(dblquad(lambda x, h: fh(h)*fx(x), T-S, Z-S, T, lambda h: h+S)[0])
                def C3(S,T,Z):
                    return cf*P3(S,T,Z)
                def V3(S,T,Z):
                    return  p*Rh(T-S)*(quad(lambda x: x*fx(x), T, Z)[0]) + p*(dblquad(lambda x, h: x*fh(h)*fx(x), T-S, Z-S, T, lambda h: h+S)[0])
                    
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

                SOMA_PROB_FALHAS = P1(S) + P2(S, T) + P3(S, T, Z)
                SOMA_VIDA = V1(S) + V2(S, T) + V3(S, T, Z) + V4(S, T) + V5(S, T, Z) + V6(S, T) + V7(S, T, Z)

                MTBOF = SOMA_PROB_FALHAS / SOMA_VIDA
                return MTBOF
            pass

            st.write('MTBOF:', MTBOF(S,T,Z))
            CR=ret.fun
            resultado_iteracao = {  # Crie um dicionário para armazenar os resultados de uma iteração
                'eta': eta,
                'beta': beta,
                'lbda': lbda,
                'p': p,
                'co': co,
                'cp': cp,
                'cv': cv,
                'cw': cw,
                'cf': cf,
                'taxa': CR,
                'S': S,
                'T': T,
                'Z': Z
            }
            resultados.append(resultado_iteracao)
            resultados_df = pd.DataFrame(resultados)
            media = resultados_df['taxa'].mean()
            desvio_padrao = resultados_df['taxa'].std()
            st.write(f'Média da Taxa de Custo: {media}')
            st.write(f'Desvio Padrão da Taxa de Custo: {desvio_padrao}')

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
