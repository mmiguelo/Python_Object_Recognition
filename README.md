<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.x-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.x-11557C?style=for-the-badge)](https://matplotlib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

<!-- PROJECT TITLE -->
<br />
<div align="center">
  <h1>🔍 Identificação Automática de Peças por Visão Computacional</h1>
  <p align="center">
    Programa em Python para identificação, classificação e quantificação automática de peças distintas numa imagem, utilizando técnicas de processamento de imagem com OpenCV.
    <br />
    <strong>Trabalho Prático 1 — Visão por Computador</strong>
    <br />
    <br />
    <a href="#funcionalidades">Funcionalidades</a>
    ·
    <a href="#como-funciona">Como Funciona</a>
    ·
    <a href="#utilização">Utilização</a>
    ·
    <a href="#resultados">Resultados</a>
  </p>
</div>

---

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Como Funciona](#como-funciona)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Utilização](#utilização)
- [Resultados](#resultados)
- [Estrutura do Projeto](#estrutura-do-projeto)

---

## 📖 Sobre o Projeto

Este projeto foi desenvolvido no âmbito da unidade curricular de **Visão por Computador** e tem como objetivo o desenvolvimento de um sistema de **reconhecimento automático de objetos** numa imagem.

O programa é capaz de:
- Ler um ficheiro de imagem (`.jpg`) escolhido pelo utilizador
- Identificar todas as peças visíveis na imagem
- Classificar cada peça segundo a sua **cor**, **forma** e **presença de furos**
- Apresentar um relatório detalhado com todas as métricas
- Gerar uma imagem anotada com a localização, centróide e características de cada peça

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## ✨ Funcionalidades

| # | Funcionalidade | Descrição |
|---|----------------|-----------|
| 1 | **Contagem total** | Número total de peças identificadas na imagem |
| 2.1 | **Classificação por cor** | Vermelho, Azul, Branco ou Indefinido |
| 2.2 | **Classificação por forma** | Circular ou Não circular (índice de circularidade) |
| 2.3 | **Deteção de furos** | Peças com/sem furos e número de furos por peça |
| 3 | **Área e perímetro** | Cálculo em pixéis para cada peça identificada |
| 3.1 | **Extremos** | Identificação das peças com maior e menor área |
| 4 | **Anotação visual** | Bounding box, centro de gravidade, tipo e características |

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## ⚙️ Como Funciona

O pipeline de processamento segue os seguintes passos:

```
Imagem de entrada (.jpg)
        │
        ▼
┌─────────────────────────┐
│   Pré-processamento     │  → Conversão HSV + Escala de cinza + Desfoque Gaussiano
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│   Segmentação           │  → Threshold Otsu (objetos claros)
│   Multi-canal           │  → + Canal de saturação (objetos coloridos)
│                         │  → + Canal de valor (exclusão do fundo)
│                         │  → Combinação + Operações morfológicas
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│  Deteção de contornos   │  → findContours com RETR_CCOMP (hierarquia)
│  + Filtragem            │  → Área mínima + exclusão de bordas
└─────────┬───────────────┘
          ▼
┌─────────────────────┐
│  Classificação      │  → Cor (HSV), Forma (circularidade), Furos (hierarquia)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Relatório +        │  → Tabela de resultados + Imagem anotada
│  Visualização       │
└─────────────────────┘
```

### Segmentação Multi-canal
A segmentação combina **três abordagens** para garantir a deteção robusta de todos os objetos, independentemente da sua cor:
1. **Threshold de Otsu** (escala de cinza) — deteta objetos claros (brancos, cinzentos, metálicos)
2. **Canal de saturação** (HSV) — deteta objetos coloridos (vermelho, azul) que podem ser escuros na escala de cinza
3. **Canal de valor** (HSV) — exclui o fundo preto puro

A máscara final é: `Otsu OR (Saturação AND Valor)`

### Deteção de Cor (HSV)
A classificação por cor é realizada no **espaço de cores HSV**, que é mais robusto a variações de iluminação do que o RGB. Para cada peça, é criada uma máscara que isola apenas os pixéis dentro do contorno, e a contagem de pixéis é feita exclusivamente sobre a área da peça (não sobre o bounding box inteiro), garantindo maior precisão.

### Classificação de Forma
A circularidade é calculada pela fórmula:

$$\text{circularidade} = \frac{4\pi \times \text{área}}{\text{perímetro}^2}$$

Um valor próximo de **1.0** indica um círculo perfeito. O limiar utilizado é **0.75**.

### Deteção de Furos
Utiliza-se a hierarquia de contornos (`RETR_CCOMP`) do OpenCV, onde:
- **Nível 0** → Contornos exteriores (peças)
- **Nível 1** → Contornos interiores (furos)

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## 📦 Requisitos

- **Python** 3.8 ou superior
- **OpenCV** (`opencv-python`)
- **NumPy**
- **Matplotlib**

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## 🚀 Instalação

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/mmiguelo/Python---Object_recognition.git
   cd Python---Object_recognition
   ```

2. **Instalar as dependências**
   ```bash
   pip install opencv-python numpy matplotlib
   ```

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## 🎯 Utilização

### Opção 1 — Modo interativo
```bash
python projecto.py
```
O programa irá solicitar o caminho para o ficheiro de imagem.

### Opção 2 — Argumento da linha de comandos
```bash
python projecto.py 4.jpg
```

### Exemplo de saída
```
======================================================================
  ANÁLISE DA IMAGEM: 4.jpg
======================================================================

  1. Número total de peças: 12

  2. Classificação das peças:
     2.1 Por cor:
         - Vermelho:  1
         - Azul:      2
         - Branco:    7
         - Indefinido:2
     2.2 Por forma:
         - Circulares:     5
         - Não circulares: 7
     2.3 Por furos:
         - Com furos:  3
         - Sem furos:  9

  3. Área e perímetro de cada peça:
     ID    Cor          Forma           Área (px)    Perímetro (px)   Furos
     ----- ------------ --------------- ------------ ---------------- ------
     1     Branco       Não circular    877          145              0
     2     Branco       Não circular    2557         422              0
     3     Branco       Não circular    866          150              0
     4     Branco       Não circular    774          146              0
     5     Branco       Circular        13229        460              1
     6     Branco       Não circular    12965        488              0
     7     Branco       Não circular    38858        860              0
     8     Vermelho     Circular        4769         261              0
     9     Indefinido   Circular        25281        594              3
     10    Azul         Circular        2729         195              0
     11    Indefinido   Não circular    20989        620              2
     12    Azul         Circular        2716         196              0

     3.1 Peça com MAIOR área: #7 (Área = 38858 px, Branco, Não circular)
         Peça com MENOR área: #4 (Área = 774 px, Branco, Não circular)

  4. Imagem anotada com bounding box, centróide e características.
======================================================================
```

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## 📊 Resultados

O programa gera uma **imagem anotada** com renderização em **duas passagens** (formas primeiro, texto por cima) para garantir legibilidade:

- 🟡 **Contorno da peça** (linha ciano/amarela)
- 🟩 **Bounding box** (retângulo verde)
- 🔴 **Centro de gravidade** (ponto vermelho)
- 📝 **Informações** — ID, cor, forma, área, perímetro e número de furos (sobrepostas por cima de tudo)

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## 📁 Estrutura do Projeto

```
Python---Object_recognition/
│
├── projecto.py          # Programa principal de análise de imagem
├── README.md            # Documentação do projeto
│
├── 1.jpg                # ┐
├── 2.jpg                # │
├── 4.jpg                # │
├── 5.jpg                # │  Imagens de teste com peças
├── 6.jpg                # │  em diferentes configurações
├── 7.jpg                # │
├── 9.jpg                # │
├── 10.jpg               # │
├── 11.jpg               # │
├── 13.jpg               # │
├── 14.jpg               # │
└── 15.jpg               # ┘
```

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

## 🛠️ Tecnologias Utilizadas

<div align="center">

| Tecnologia | Utilização |
|:---:|:---|
| <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="40"/> | **Python** — Linguagem de programação principal |
| <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/opencv/opencv-original.svg" width="40"/> | **OpenCV** — Processamento de imagem e deteção de contornos |
| <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/numpy/numpy-original.svg" width="40"/> | **NumPy** — Manipulação de arrays e operações numéricas |
| <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/matplotlib/matplotlib-original.svg" width="40"/> | **Matplotlib** — Visualização e apresentação de resultados |

</div>

<p align="right">(<a href="#readme-top">⬆️ topo</a>)</p>

---

<div align="center">
  <sub>Desenvolvido para a unidade curricular de <strong>Visão por Computador</strong></sub>
</div>
