import asyncio
import os
from playwright.async_api import async_playwright

class Datasusextractor:
    
    def __init__(self, output_dir="data/raw"):
        # URL da Produção Ambulatorial Brasil (SIA/SUS)
        self.url = "http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qabr.def"
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def select_smart(self, page, selector, text_to_find):
        try:
            await page.select_option(selector, label=text_to_find)
        except Exception:
            options = await page.locator(f"{selector} option").all_text_contents()
            for opt in options:
                if text_to_find.lower() in opt.lower():
                    await page.select_option(selector, label=opt)
                    return
            raise

    def gerar_periodos(self):
        """Gera a lista de Jan/2024 até Jan/2026 (25 meses) no formato do Tabnet"""
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        lista_final = []
        
        # Anos de 2024 a 2026
        for ano in [2024, 2025, 2026]:
            for mes in meses:
                # Condição para parar em Jan/2026
                if ano == 2026 and mes != "Jan":
                    break
                lista_final.append(f"{mes}/{ano}")
        
        # Inverter para começar do mais recente (opcional, mas comum no Tabnet)
        return lista_final[::-1]

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"Acessando: {self.url}")
            await page.goto(self.url, wait_until="networkidle")

            # Configurações fixas: Linha e Coluna
            await self.select_smart(page, 'select[name="Linha"]', "Município")
            await self.select_smart(page, 'select[name="Coluna"]', "Subgrupo proced.")

            conteudos = ["Qtd.aprovada", "Valor aprovado"]
            periodos = self.gerar_periodos()

            print(f"Total de períodos a processar: {len(periodos)}")

            for conteudo in conteudos:
                print(f"\n=== EXTRAINDO: {conteudo} ===")
                await self.select_smart(page, 'select[name="Incremento"]', conteudo)

                for periodo in periodos:
                    try:
                        print(f"--- Processando: {periodo} ---")
                        await page.select_option('select[name="Arquivos"]', label=periodo)

                        # Scroll e Configurações de Formato
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        
                        # Marcar linhas zeradas
                        zeradas = page.locator('input[name="zeradas"]')
                        if await zeradas.count() > 0: await zeradas.check()

                        # Marcar colunas separadas por ;
                        selector_csv = "//input[@type='radio' and contains(following-sibling::text(), ';')]"
                        try:
                            await page.locator(selector_csv).click(timeout=3000)
                        except:
                            pass

                        # Clicar em Mostrar e Capturar nova aba
                        botao_mostra = 'input[name="mostra"], input[value="Mostra"], input[type="submit"]'
                        async with context.expect_page() as new_page_info:
                            await page.click(botao_mostra)
                        
                        results_page = await new_page_info.value
                        await results_page.wait_for_load_state("networkidle")

                        # EXTRAÇÃO DE TEXTO (Ajuste para o quadrado azul)
                        print("Capturando dados da tela...")
                        elemento_dados = results_page.locator("pre")
                        
                        if await elemento_dados.count() > 0:
                            conteudo_csv = await elemento_dados.inner_text()
                        else:
                            # Caso não ache <pre>, pega o texto do body filtrando o que interessa
                            conteudo_csv = await results_page.inner_text("body")

                        # Salvar arquivo
                        tipo = "qtd" if "Qtd" in conteudo else "valor"
                        clean_per = periodo.replace('/', '_')
                        filename = f"sia_br_{tipo}_{clean_per}.csv"
                        path = os.path.join(self.output_dir, filename)

                        with open(path, "w", encoding="utf-8") as f:
                            f.write(conteudo_csv)
                        
                        print(f"✅ Arquivo salvo: {filename}")
                        await results_page.close()
                        await asyncio.sleep(1) # Delay para evitar bloqueio do servidor

                    except Exception as e:
                        print(f"❌ Erro em {periodo}: {e}")
                        await page.goto(self.url, wait_until="networkidle")
                        # Re-seleciona o básico em caso de reload
                        await self.select_smart(page, 'select[name="Linha"]', "Município")
                        await self.select_smart(page, 'select[name="Coluna"]', "Subgrupo proced.")
                        await self.select_smart(page, 'select[name="Incremento"]', conteudo)

            await browser.close()

if __name__ == "__main__":
    extractor = Datasusextractor()
    asyncio.run(extractor.run())