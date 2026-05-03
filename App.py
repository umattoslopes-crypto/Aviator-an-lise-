def extrair_velas_print(img):
    img_np = np.array(img.convert('RGB'))
    h, w = img_np.shape[:2]

    # 🔥 corte da área da grade (ajustado pro seu print)
    img_np = img_np[int(h*0.50):int(h*0.88), int(w*0.08):int(w*0.78)]

    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)

    # 🎯 máscaras de cor (verde e vermelho)
    mask_verde = cv2.inRange(hsv, (40, 50, 50), (90, 255, 255))
    mask_vermelho1 = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
    mask_vermelho2 = cv2.inRange(hsv, (170, 50, 50), (180, 255, 255))

    mask = mask_verde | mask_vermelho1 | mask_vermelho2

    # limpa ruído
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    itens = []

    for cnt in contornos:
        x, y, w_box, h_box = cv2.boundingRect(cnt)

        if w_box < 40 or h_box < 20:
            continue

        recorte = img_np[y:y+h_box, x:x+w_box]

        gray = cv2.cvtColor(recorte, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        textos = reader.readtext(thresh, detail=0, allowlist='0123456789.x')

        for t in textos:
            t = t.lower().replace(',', '.').strip()

            if 'x' not in t:
                continue

            match = re.findall(r"\d+\.\d+x", t)

            if match:
                try:
                    valor = float(match[0].replace('x',''))

                    # evita lixo (tipo 500)
                    if 1.0 <= valor <= 200:
                        itens.append({
                            'x': x,
                            'y': y,
                            'v': valor
                        })
                except:
                    pass

    # 🔥 organizar por linhas
    linhas = []
    tol = 20

    for item in sorted(itens, key=lambda i: i['y']):
        colocado = False
        for linha in linhas:
            if abs(linha[0]['y'] - item['y']) < tol:
                linha.append(item)
                colocado = True
                break
        if not colocado:
            linhas.append([item])

    # 🔥 ordem: topo → baixo, direita → esquerda
    linhas.sort(key=lambda l: l[0]['y'])

    velas = []

    for linha in linhas:
        linha.sort(key=lambda i: -i['x'])
        for item in linha:
            velas.append(f"{item['v']:.2f}x")  # 👈 já retorna com "x"

    return velas
