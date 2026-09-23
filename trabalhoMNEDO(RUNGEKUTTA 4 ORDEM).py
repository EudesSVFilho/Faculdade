import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd
import seaborn as sns

## Função que define o sistema de equações diferenciais

def reator(t,y,c1, c2, c3):

    g = y[0]
    dgdt = c1 * g - c2 * g**2
    dfdt = c3 * g
    return np.array([dgdt, dfdt])

## Implementação do método de Runge-Kutta de quarta ordem (RK4)

def rk4(f, t0, y0, T, n,c1, c2, c3):
    t_valores = [t0]
    y_valores = [y0]
    
    t = t0
    y = y0
    for i in range(n):
        k1 = T * f(t, y, c1, c2, c3)
        k2 = T * f(t + 0.5 * T, y + 0.5 * k1, c1, c2, c3)
        k3 = T * f(t + 0.5 * T, y + 0.5 * k2, c1, c2, c3)
        k4 = T * f(t + T, y + k3, c1, c2, c3)
        y = y + (k1 + 2 * k2 + 2 * k3 + k4) / 6
        t = t + T
        t_valores.append(t)
        y_valores.append(y)

    return t_valores, y_valores

## Parâmetros iniciais e simulação

temp_init = 0
temp_fim = 1
g_init = 0.03
f_init = 0
dt = [0.3, 0.1, 0.08, 0.05, 0.025,]

dados_simulacoes = {} # Armazena os dados de cada simulação

## Correndo as simulações para diferentes valores de dt e constantes

for i in range(3):
    todos_os_dados = {}  # Armazena todos os dados das simulações
## Entrada de constantes e garantia de uso das constantes padrão na primeira simulação

    if i == 0:
        print("Usando constantes padrão do trabalho:")
        c1, c2, c3 =  13.1, 13.94, 1.71
        simulacao= 'Constantes Padrão'
    else: 
        print(f"Simulação de numero {i+1}:")
        c1 = float(input("Digite o valor da primeira constante: "))
        c2 = float(input("Digite o valor da segunda constante: "))
        c3 = float(input("Digite o valor da terceira constante: "))
        simulacao= f'Simulação {i+1}'
## Loop para diferentes valores de dt

    for dt1 in dt:
            T = dt1
            t0 = temp_init
            tf = temp_fim
            y0 = [g_init, f_init]
            n = int((tf - t0) / T)


            print(f"Simulação com dt = {T}, n = {n}\n")
            t_valores, y_valores = rk4(reator, t0, y0, T, n, c1, c2, c3)

## Separando os valores de g e f
        
            g_valores = [y[0] for y in y_valores]
            f_valores = [y[1] for y in y_valores]

            todos_os_dados[T] = {
            'tempo': t_valores,
            'g': g_valores,
            'f': f_valores
        }
            resultados = todos_os_dados[T]


    dados_simulacoes[simulacao] = todos_os_dados.copy()
    print("Simulação concluída para todos os passos de tempo.")

for dt1 in dt:
    lista_de_dfs = [pd.DataFrame({
                        'Tempo': dados[dt1]['tempo'],
                        f'G ({simulacao})': dados[dt1]['g'],
                        f'F ({simulacao})': dados[dt1]['f']
                     }).set_index('Tempo')
                     for simulacao, dados in dados_simulacoes.items()]
    
    df_final = pd.concat(lista_de_dfs, axis=1)
    nome_arquivo = f"resultados dt={dt1}.csv".replace('.', ',')
    df_final.to_csv(nome_arquivo, sep='|', float_format='%.6f')
    print(f"Arquivo salvo em: {nome_arquivo}")


## Salvando os resultados em um arquivo CSV
sns.set_style("whitegrid")
sns.set_palette("rocket")

marcador = ['o', 's', '^', 'D','*']
linha = ['-', '--', ':', '-.', '-']

# GRÁFICO 1: ANÁLISE DE CONVERGÊNCIA (para cada simulação)
for simulacao, dados in dados_simulacoes.items():
    # Gráfico de G
    plt.figure(figsize=(12, 7))
    plt.title(f'Análise de Convergência de G - {simulacao}', fontsize=16)
    for i, (dt_valor, resultados) in enumerate(dados.items()):
        plt.plot(resultados['tempo'], resultados['g'], label=f'dt={dt_valor}',
                 marker=marcador[i], linestyle=linha[i], markersize=5)
    plt.xlabel('Tempo (s)', fontsize=12)
    plt.ylabel('Concentração de G', fontsize=12)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.show()

    # Gráfico de F
    plt.figure(figsize=(12, 7))
    plt.title(f'Análise de Convergência de F - {simulacao}', fontsize=16)
    for i, (dt_valor, resultados) in enumerate(dados.items()):
        plt.plot(resultados['tempo'], resultados['f'], label=f'dt={dt_valor}',
                 marker=marcador[i], linestyle=linha[i], markersize=5)
    plt.xlabel('Tempo (s)', fontsize=12)
    plt.ylabel('Concentração de F', fontsize=12)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.show()

# GRÁFICO 2: ANÁLISE DE SENSIBILIDADE
menor_dt = 0.05
print(f"\n... Gerando gráficos de sensibilidade comparando as simulações (usando dt={menor_dt})...")

# Gráfico comparativo para G
plt.figure(figsize=(12, 7))
plt.title(f'Análise de Sensibilidade de G (dt={menor_dt})', fontsize=16)
cores_sensibilidade = sns.color_palette("rocket", n_colors=len(dados_simulacoes))
for i, (simulacao, dados) in enumerate(dados_simulacoes.items()):
    resultados_precisos = dados[menor_dt]
    plt.plot(resultados_precisos['tempo'], resultados_precisos['g'],
             label=simulacao, color=cores_sensibilidade[i], linestyle='-')
plt.xlabel('Tempo (s)', fontsize=12)
plt.ylabel('Concentração de G', fontsize=12)
plt.legend(fontsize=10)
plt.tight_layout()
plt.show()

# Gráfico comparativo para F
plt.figure(figsize=(12, 7))
plt.title(f'Análise de Sensibilidade de F (dt={menor_dt})', fontsize=16)
cores_sensibilidade = sns.color_palette("rocket", n_colors=len(dados_simulacoes))
for i, (simulacao, dados) in enumerate(dados_simulacoes.items()):
    resultados_precisos = dados[menor_dt]
    plt.plot(resultados_precisos['tempo'], resultados_precisos['f'],
             label=simulacao, color=cores_sensibilidade[i], linestyle='-')
plt.xlabel('Tempo (s)', fontsize=12)
plt.ylabel('Concentração de F', fontsize=12)
plt.legend(fontsize=10)
plt.tight_layout()
plt.show() 