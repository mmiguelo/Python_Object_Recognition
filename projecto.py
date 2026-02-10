import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# =============================================================================
# Configurações
# =============================================================================
MIN_CONTOUR_AREA = 500       # Área mínima (pixéis) para considerar um contorno como peça
CIRCULARITY_THRESHOLD = 0.75  # Limiar de circularidade (1.0 = círculo perfeito)


# =============================================================================
# Função para detectar a cor dominante de uma peça usando o espaço HSV
# =============================================================================
def detect_color(roi_bgr, mask=None):
    """
    Detecta a cor dominante de uma região de interesse (ROI).
    Utiliza o espaço de cores HSV que é mais robusto a variações de iluminação
    do que o espaço RGB/BGR.
    Se uma máscara for fornecida, apenas os pixéis dentro da máscara são considerados.
    Retorna: "Vermelho", "Azul", "Branco" ou "Indefinido".
    """
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

    # --- Vermelho (o vermelho em HSV envolve dois intervalos: 0-10 e 160-180) ---
    red_lower1 = np.array([0, 70, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([160, 70, 50])
    red_upper2 = np.array([180, 255, 255])
    red_mask = cv2.inRange(hsv, red_lower1, red_upper1) | cv2.inRange(hsv, red_lower2, red_upper2)

    # --- Azul ---
    blue_lower = np.array([90, 70, 50])
    blue_upper = np.array([130, 255, 255])
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)

    # --- Branco (saturação baixa e valor alto) ---
    white_lower = np.array([0, 0, 180])
    white_upper = np.array([180, 60, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)

    # Aplicar máscara do contorno se fornecida (contar apenas pixéis da peça)
    if mask is not None:
        red_mask = cv2.bitwise_and(red_mask, mask)
        blue_mask = cv2.bitwise_and(blue_mask, mask)
        white_mask = cv2.bitwise_and(white_mask, mask)
        total_pixels = cv2.countNonZero(mask)
    else:
        total_pixels = roi_bgr.shape[0] * roi_bgr.shape[1]

    if total_pixels == 0:
        return "Indefinido"

    red_ratio = cv2.countNonZero(red_mask) / total_pixels
    blue_ratio = cv2.countNonZero(blue_mask) / total_pixels
    white_ratio = cv2.countNonZero(white_mask) / total_pixels

    # A cor com maior percentagem de pixéis ganha (com mínimo de 10%)
    threshold = 0.10
    ratios = {"Vermelho": red_ratio, "Azul": blue_ratio, "Branco": white_ratio}
    best_color = max(ratios, key=ratios.get)

    if ratios[best_color] >= threshold:
        return best_color
    else:
        return "Indefinido"


# =============================================================================
# Função para verificar se um contorno é circular
# =============================================================================
def is_circular(contour):
    """
    Verifica se um contorno é circular usando o índice de circularidade:
        circularidade = 4 * pi * area / perimetro^2
    Um círculo perfeito tem circularidade = 1.0.
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return False
    circularity = (4 * np.pi * area) / (perimeter * perimeter)
    return circularity >= CIRCULARITY_THRESHOLD


# =============================================================================
# Função para contar furos de uma peça usando a hierarquia de contornos
# =============================================================================
def count_holes(contour_index, hierarchy):
    """
    Conta o número de furos (contornos filhos) de uma peça.
    Na hierarquia do OpenCV (RETR_CCOMP), os contornos de nível 0 são exteriores
    e os de nível 1 são os furos (filhos diretos).
    hierarchy[0][i] = [next, previous, first_child, parent]
    """
    holes = 0
    # Obtemos o primeiro filho do contorno
    child = hierarchy[0][contour_index][2]
    while child != -1:
        holes += 1
        # Passamos ao próximo irmão do filho
        child = hierarchy[0][child][0]
    return holes


# =============================================================================
# Função para calcular área e perímetro
# =============================================================================
def get_area_and_perimeter(contour):
    """Calcula a área e o perímetro de um contorno."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    return area, perimeter


# =============================================================================
# Função para calcular o centro de gravidade (centróide) de um contorno
# =============================================================================
def get_centroid(contour):
    """Calcula o centróide de um contorno usando momentos."""
    M = cv2.moments(contour)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        x, y, w, h = cv2.boundingRect(contour)
        cx, cy = x + w // 2, y + h // 2
    return cx, cy


# =============================================================================
# Função para anotar a imagem com bounding box, centróide e informações
# =============================================================================
def annotate_piece_text(img, piece_info):
    """
    Desenha APENAS o texto com informações da peça sobre a imagem.
    As formas (bounding box, contorno, centróide) são desenhadas numa passagem anterior
    para garantir que o texto fica sempre por cima e legível.
    """
    piece_id = piece_info["id"]
    color_name = piece_info["cor"]
    shape_name = piece_info["forma"]
    area = piece_info["area"]
    perimeter = piece_info["perimetro"]
    num_holes = piece_info["furos"]
    x, y, w, h = piece_info["bounding_box"]

    # Preparar texto — Posicionar acima da bounding box
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.30
    thickness = 1
    line_spacing = 14

    texts = [
        f"#{piece_id} | {color_name} | {shape_name}",
        f"A={int(area)}px  P={int(perimeter)}px",
        f"Furos: {num_holes}",
    ]

    # Posição inicial do texto (acima da bounding box)
    text_y = y - 10
    for i, txt in enumerate(reversed(texts)):
        ty = text_y - i * line_spacing
        if ty < 15:
            ty = y + h + 15 + i * line_spacing  # Se não houver espaço acima, colocar abaixo
        # Fundo escuro para legibilidade
        (tw, th_text), _ = cv2.getTextSize(txt, font, font_scale, thickness)
        cv2.rectangle(img, (x, ty - th_text - 2), (x + tw + 4, ty + 4), (0, 0, 0), -1)
        cv2.putText(img, txt, (x + 2, ty), font, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)


# =============================================================================
# Função principal de processamento
# =============================================================================
def process_image(image_path):
    """Processa uma imagem, identifica e classifica todas as peças visíveis."""

    img = cv2.imread(image_path)
    if img is None:
        print(f"Erro: Não foi possível abrir o ficheiro '{image_path}'.")
        return

    print("=" * 70)
    print(f"  ANÁLISE DA IMAGEM: {os.path.basename(image_path)}")
    print("=" * 70)

    # --- Pré-processamento ---
    # Converter para HSV e escala de cinza
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Aplicar desfoque gaussiano para reduzir ruído
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 1) Thresholding Otsu na escala de cinza (deteta objetos claros: branco, cinza, metal)
    _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 2) Canal de saturação — objetos coloridos (vermelho, azul) têm saturação alta
    #    mesmo que sejam escuros na escala de cinza
    sat = hsv[:, :, 1]
    sat_blurred = cv2.GaussianBlur(sat, (5, 5), 0)
    _, thresh_sat = cv2.threshold(sat_blurred, 50, 255, cv2.THRESH_BINARY)

    # 3) Canal de valor (brilho) — para excluir o fundo preto puro
    val = hsv[:, :, 2]
    val_blurred = cv2.GaussianBlur(val, (5, 5), 0)
    _, thresh_val = cv2.threshold(val_blurred, 40, 255, cv2.THRESH_BINARY)

    # Combinar: objetos claros (Otsu) OU objetos coloridos (saturação alta E não preto)
    thresh = thresh_otsu | (thresh_sat & thresh_val)

    # Operações morfológicas para limpar ruído (kernel pequeno para não fundir peças próximas)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    # --- Encontrar contornos com hierarquia (RETR_CCOMP) ---
    # RETR_CCOMP organiza em 2 níveis: contornos exteriores (nível 0) e furos (nível 1)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    if hierarchy is None:
        print("Nenhuma peça encontrada na imagem.")
        return

    # --- Variáveis de contagem ---
    total_pieces = 0
    circular_pieces = 0
    non_circular_pieces = 0
    color_counts = {"Vermelho": 0, "Azul": 0, "Branco": 0, "Indefinido": 0}
    pieces_with_holes = 0
    pieces_without_holes = 0
    pieces_info = []  # Lista de dicionários com informação de cada peça

    # Criar cópia da imagem para anotar
    img_annotated = img.copy()
    img_h, img_w = img.shape[:2]

    # --- Processar cada contorno de nível 0 (contornos exteriores = peças) ---
    for i in range(len(contours)):
        # Apenas contornos de nível 0 (sem pai => parent == -1)
        if hierarchy[0][i][3] != -1:
            continue  # Este contorno é um furo (filho), não uma peça

        contour = contours[i]
        area, perimeter = get_area_and_perimeter(contour)

        # Filtrar contornos demasiado pequenos (ruído)
        if area < MIN_CONTOUR_AREA:
            continue

        # Filtrar contornos que tocam as bordas da imagem (artefactos)
        x, y, w, h = cv2.boundingRect(contour)
        if x == 0 or y == 0 or (x + w) >= img_w or (y + h) >= img_h:
            continue

        total_pieces += 1
        piece_id = total_pieces

        # --- Cor ---
        roi = img[y:y + h, x:x + w]
        # Criar máscara para considerar apenas pixéis dentro do contorno
        mask_roi = np.zeros(roi.shape[:2], dtype=np.uint8)
        contour_shifted = contour - np.array([x, y])
        cv2.drawContours(mask_roi, [contour_shifted], -1, 255, -1)
        color_name = detect_color(roi, mask_roi)
        color_counts[color_name] += 1

        # --- Forma ---
        circular = is_circular(contour)
        shape_name = "Circular" if circular else "Não circular"
        if circular:
            circular_pieces += 1
        else:
            non_circular_pieces += 1

        # --- Furos ---
        num_holes = count_holes(i, hierarchy)
        if num_holes > 0:
            pieces_with_holes += 1
        else:
            pieces_without_holes += 1

        # --- Guardar informação da peça ---
        cx, cy = get_centroid(contour)
        piece_info = {
            "id": piece_id,
            "cor": color_name,
            "forma": shape_name,
            "area": area,
            "perimetro": perimeter,
            "furos": num_holes,
            "centroide": (cx, cy),
            "bounding_box": (x, y, w, h),
            "contour": contour,
        }
        pieces_info.append(piece_info)

    # --- PRIMEIRA PASSAGEM: desenhar formas (bounding boxes, contornos, centróides) ---
    for p in pieces_info:
        contour = p["contour"]
        x, y, w, h = p["bounding_box"]
        cx, cy = p["centroide"]

        # Desenhar contorno da peça
        cv2.drawContours(img_annotated, [contour], -1, (255, 255, 0), 2)
        # Desenhar bounding box
        cv2.rectangle(img_annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Desenhar centro de gravidade
        cv2.circle(img_annotated, (cx, cy), 6, (0, 0, 255), -1)

    # --- SEGUNDA PASSAGEM: desenhar textos (por cima de tudo para legibilidade) ---
    for p in pieces_info:
        annotate_piece_text(img_annotated, p)

    # =========================================================================
    # Imprimir resultados
    # =========================================================================
    if total_pieces == 0:
        print("Nenhuma peça foi identificada na imagem.")
        return

    print(f"\n  1. Número total de peças: {total_pieces}\n")

    print("  2. Classificação das peças:")
    print(f"     2.1 Por cor:")
    print(f"         - Vermelho:  {color_counts['Vermelho']}")
    print(f"         - Azul:      {color_counts['Azul']}")
    print(f"         - Branco:    {color_counts['Branco']}")
    print(f"         - Indefinido:{color_counts['Indefinido']}")
    print(f"     2.2 Por forma:")
    print(f"         - Circulares:     {circular_pieces}")
    print(f"         - Não circulares: {non_circular_pieces}")
    print(f"     2.3 Por furos:")
    print(f"         - Com furos:  {pieces_with_holes}")
    print(f"         - Sem furos:  {pieces_without_holes}")

    print(f"\n  3. Área e perímetro de cada peça:")
    print(f"     {'ID':<5} {'Cor':<12} {'Forma':<15} {'Área (px)':<12} {'Perímetro (px)':<16} {'Furos':<6}")
    print(f"     {'-'*5} {'-'*12} {'-'*15} {'-'*12} {'-'*16} {'-'*6}")
    for p in pieces_info:
        print(f"     {p['id']:<5} {p['cor']:<12} {p['forma']:<15} {int(p['area']):<12} {int(p['perimetro']):<16} {p['furos']:<6}")

    # Peça com maior e menor área
    max_piece = max(pieces_info, key=lambda p: p["area"])
    min_piece = min(pieces_info, key=lambda p: p["area"])
    print(f"\n     3.1 Peça com MAIOR área: #{max_piece['id']} "
          f"(Área = {int(max_piece['area'])} px, {max_piece['cor']}, {max_piece['forma']})")
    print(f"         Peça com MENOR área: #{min_piece['id']} "
          f"(Área = {int(min_piece['area'])} px, {min_piece['cor']}, {min_piece['forma']})")

    print(f"\n  4. Imagem anotada com bounding box, centróide e características.")
    print("=" * 70)

    # =========================================================================
    # Exibir imagem anotada
    # =========================================================================
    plt.figure(figsize=(14, 10))
    plt.imshow(cv2.cvtColor(img_annotated, cv2.COLOR_BGR2RGB))
    plt.title(f"Análise de peças — {os.path.basename(image_path)}", fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


# =============================================================================
# Ponto de entrada — Solicitar ficheiro ao utilizador
# =============================================================================
if __name__ == "__main__":
    # Verificar se foi passado como argumento da linha de comandos
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("Introduza o caminho para a imagem (ficheiro *.jpg): ").strip()

    # Verificar se o ficheiro existe
    if not os.path.isfile(image_path):
        print(f"Erro: O ficheiro '{image_path}' não foi encontrado.")
        sys.exit(1)

    if not image_path.lower().endswith(".jpg"):
        print("Aviso: O ficheiro não tem extensão .jpg. A tentar processar mesmo assim...")

    process_image(image_path)