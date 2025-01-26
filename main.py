import requests
import json
import time
import numpy as np
import os
from colorama import Fore, Style
from dotenv import load_dotenv
import winsound

# Carregar as variáveis do arquivo .env
load_dotenv()

# Configuração da API
API = os.getenv("API_WINDICE")
WINDICE_BASE_URL = os.getenv("URL_WINDICE")


# Classe Windice para interagir com a API
class Windice:
    def __init__(self, api, base_url):
        self.api = api
        self.base_url = base_url

    # Obter o saldo do usuário
    def get_user(self):
        response = requests.get(
            self.base_url + "/user",
            headers={"Authorization": self.api},
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao fazer a requisição: {response.status_code}")
            quit()

    def create_bet_data(self, curr, bet_amount, game_bool, low, high):
        if low < 0:
            print("Escolha acima de  0")
            quit()
        elif high > 9999:
            print("Escolha abaixo de 9999")
            quit()

        data = {
            "curr": curr,
            "bet": bet_amount,
            "game": game_bool,
            "low": low,
            "high": high,
        }
        return data

    # Realizar uma aposta única
    def make_single_bet(self, curr, bet_amount, game_bool, low, high):
        bet_data = self.create_bet_data(curr, bet_amount, game_bool, low, high)
        result = self.roll(bet_data)
        return result

    # Fazer o roll da aposta
    def roll(self, bet_data):
        response = requests.post(
            self.base_url + "/roll",
            headers={"Content-type": "application/json", "Authorization": self.api},
            data=json.dumps(bet_data),
        )
        if response.status_code == 200:
            res = response.json()
            if res["status"] == "success" and "data" in res:
                return res["data"]
            else:
                print(f"Erro ao fazer a aposta: {res['message']}")
                return None
        else:
            print(f"Erro ao fazer a requisição: {response.status_code}")
            return None


def makeBet(windice, betData):
    try:
        dados_usuario_windice = windice.get_user()  # Verifica o saldo atual do usuário

        # Valida os dados retornados pelo serviço
        if not dados_usuario_windice or "data" not in dados_usuario_windice:
            print(
                Fore.RED + "Erro: Dados do usuário não encontrados." + Style.RESET_ALL
            )
            return

        # Extrai os dados relevantes
        user_data = dados_usuario_windice["data"]
        username = user_data.get("username", "Usuário desconhecido")
        user_hash = user_data.get("hash", "Hash não disponível")
        balance = user_data.get("balance", {}).get(
            betData["currency"], "Saldo indisponível"
        )

        # Exibe os dados formatados
        print("===============================")
        print(Fore.YELLOW + "===== DADOS DE USUÁRIO =====" + Style.RESET_ALL)
        print(
            Fore.YELLOW
            + f"Usuário: {username} | UserHash: {user_hash}"
            + Style.RESET_ALL
        )
        print(Fore.YELLOW + f"Moeda Atual: {betData['currency']}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Saldo: {balance}" + Style.RESET_ALL)

        print(Fore.YELLOW + f"===== REALIZANDO JOGADA =====" + Style.RESET_ALL)

        if balance < betData["basebet"]:
            print(
                Fore.RED
                + f"VOCÊ ESTÁ SEM SALDO! RECARREGUE SUA WALLET!"
                + Style.RESET_ALL
            )
            winsound.PlaySound("sound_lose.wav", winsound.SND_ALIAS)
        else:
            makeOneBet = windice.make_single_bet(
                betData["currency"],
                betData["basebet"],
                betData["game_side"],
                betData["chance_low"],
                betData["chance_high"],
            )
            save_logs(makeOneBet)
            return makeOneBet

    except Exception as e:
        print(Fore.RED + f"Erro ao executar a aposta: {e}" + Style.RESET_ALL)


def save_logs(log_data):
    """
    Salva dados em um único arquivo de log, mantendo o formato JSON correto.
    """
    import os
    import json
    from colorama import Fore, Style

    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_file = os.path.join(logs_dir, "bets.json")

    # Verifica se o arquivo já existe e carrega o conteúdo existente
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                existing_logs = json.load(f)  # Lê os logs existentes
            except json.JSONDecodeError:
                existing_logs = (
                    []
                )  # Inicia um novo array se o JSON estiver vazio ou inválido
    else:
        existing_logs = []  # Caso o arquivo não exista, inicia um novo array

    # Adiciona a nova entrada ao array de logs
    existing_logs.append(log_data)

    # Escreve o array completo de volta no arquivo
    with open(log_file, "w") as f:
        json.dump(
            existing_logs, f, indent=4
        )  # Salva com indentação para facilitar a leitura

    print(
        Fore.LIGHTBLACK_EX
        + f"[LOG] Informações salvas no arquivo: {log_file}"
        + Style.RESET_ALL
    )


def save_state(state_data):
    """Salva os dados no arquivo state.json."""
    with open("state.json", "w") as file:
        json.dump(state_data, file, indent=4)
    print(
        Fore.LIGHTBLACK_EX
        + "[INFO] Estado salvo no arquivo state.json."
        + Style.RESET_ALL
    )


def initialize_intervals():
    """Inicializa os intervalos com valores zerados."""
    low_range = range(
        int(os.getenv("ANALISE_RESULTADO_INICIAL_LOW")),
        int(os.getenv("ANALISE_RESULTADO_FINAL_LOW")) + 1,
    )
    high_range = range(
        int(os.getenv("ANALISE_RESULTADO_INICIAL_HIGH")),
        int(os.getenv("ANALISE_RESULTADO_FINAL_HIGH")) + 1,
    )

    intervals = {
        "low": {str(i): 0 for i in low_range},
        "high": {str(i): 0 for i in high_range},
    }
    return intervals


def load_state():
    """Carrega os dados do arquivo state.json ou retorna valores padrão."""
    try:
        if os.path.exists("state.json") and os.path.getsize("state.json") > 0:
            with open("state.json", "r") as file:
                state_data = json.load(file)
                print(
                    Fore.LIGHTBLACK_EX
                    + "[INFO] Estado carregado do arquivo state.json."
                    + Style.RESET_ALL
                )
                return state_data
    except (json.JSONDecodeError, IOError) as e:
        print(
            Fore.YELLOW
            + f"[AVISO] Erro ao carregar state.json: {str(e)}"
            + Style.RESET_ALL
        )

    # Se arquivo não existe, está vazio ou tem erro, cria estado padrão
    default_state = {
        "game_mode": 1,
        "bet_count": 0,
        "win_count": 0,
        "lose_count": 0,
        "target_low_count": 0,
        "target_high_count": 0,
        "game_play_side": "",
        "nextbet": float(os.getenv("BASEBET_ANALISE")),
        "intervals": initialize_intervals(),
    }

    # Salva o estado padrão no arquivo
    with open("state.json", "w") as file:
        json.dump(default_state, file, indent=4)

    print(
        Fore.LIGHTBLACK_EX
        + "[INFO] Novo arquivo state.json criado com valores padrão."
        + Style.RESET_ALL
    )

    return default_state


# Função do bot para realizar apostas reais
def bot(windice, pre_roll, state):
    dados_usuario_windice = windice.get_user()

    # Apostas reais com base na estratégia
    if pre_roll > 0:
        for i in range(pre_roll):

            gameLog = gameLogic(windice, state)
            if gameLog == True:
                print(
                    Fore.GREEN
                    + f"Saldo Atualizado: {dados_usuario_windice['data']['balance'][os.getenv("MOEDA_LUCRO")]}"
                    + Style.RESET_ALL
                )
                break

    else:
        while True:
            gameLog = gameLogic(windice, state)
            if gameLog == True:
                print(
                    Fore.GREEN
                    + f"Saldo Atualizado: {dados_usuario_windice['data']['balance'][os.getenv("MOEDA_LUCRO")]}"
                    + Style.RESET_ALL
                )
                break


def gameLogic(windice, state):
    print("")
    if state["game_mode"] == 1:
        state["nextbet"] = float(os.getenv("BASEBET_ANALISE"))
        print(Fore.CYAN + f"JOGANDO EM MODO DE ANÁLISE" + Style.RESET_ALL)
        betData = {
            "game_mode": state["game_mode"],
            "currency": os.getenv("MOEDA_ANALISE"),
            "basebet": state["nextbet"],
            "chance_low": int(os.getenv("CHANCE_LOW_ANALISE")),
            "chance_high": int(os.getenv("CHANCE_HIGH_ANALISE")),
            "game_side": os.getenv("POSICAO_ANALISE"),
        }

        resultBet = makeBet(windice, betData)

        if resultBet:
            state["bet_count"] += 1
            state["target_low_count"] += 1
            state["target_high_count"] += 1

            result = resultBet["result"]

            if result >= int(
                os.getenv("ANALISE_RESULTADO_INICIAL_LOW")
            ) and result <= int(os.getenv("ANALISE_RESULTADO_FINAL_LOW")):
                state["intervals"]["low"][str(result)] += 1
                state["target_low_count"] = 0

            if result >= int(
                os.getenv("ANALISE_RESULTADO_INICIAL_HIGH")
            ) and result <= int(os.getenv("ANALISE_RESULTADO_FINAL_HIGH")):
                state["intervals"]["high"][str(result)] += 1
                state["target_high_count"] = 0

            if int(state["target_low_count"]) >= int(os.getenv("QUANTIDADE_ANALISE")):
                state["game_mode"] = 2
                state["game_play_side"] = "low"
                state["bet_count"] = 0
                state["target_low_count"] = 0
                state["nextbet"] = float(os.getenv("BASEBET_LUCRO"))

            if int(state["target_high_count"]) >= int(os.getenv("QUANTIDADE_ANALISE")):
                state["game_mode"] = 2
                state["game_play_side"] = "high"
                state["bet_count"] = 0
                state["target_high_count"] = 0
                state["nextbet"] = float(os.getenv("BASEBET_LUCRO"))

            print(Fore.LIGHTBLACK_EX + "===== CONTADORES =====" + Style.RESET_ALL)
            print(Fore.LIGHTBLACK_EX + f"ROLLS: {state['bet_count']}" + Style.RESET_ALL)
            print(
                Fore.LIGHTBLACK_EX
                + f"CONTA LOW: {state['target_low_count']}"
                + Style.RESET_ALL
            )
            print(
                Fore.LIGHTBLACK_EX
                + f"CONTA HIGH: {state['target_high_count']}"
                + Style.RESET_ALL
            )
            print(Fore.LIGHTBLUE_EX + f"NÚMERO SORTEADO: {result}" + Style.RESET_ALL)
            print(
                Fore.LIGHTBLUE_EX
                + f"INTERVALOS LOW: {state['intervals']['low']}"
                + Style.RESET_ALL
            )
            print(
                Fore.LIGHTBLUE_EX
                + f"INTERVALOS HIGH: {state['intervals']['high']}"
                + Style.RESET_ALL
            )
            save_state(state)
    else:
        print(Fore.CYAN + f"JOGANDO EM MODO DE LUCRO" + Style.RESET_ALL)

        if os.getenv("POSICAO_LUCRO") == "out":
            betData = {
                "game_mode": state["game_mode"],
                "currency": os.getenv("MOEDA_LUCRO"),
                "basebet": state["nextbet"],
                "chance_low": int(os.getenv("ANALISE_RESULTADO_FINAL_LOW")),
                "chance_high": int(os.getenv("ANALISE_RESULTADO_INICIAL_HIGH")),
                "game_side": "out",
            }

        else:
            if state["game_play_side"] == "low":
                betData = {
                    "game_mode": state["game_mode"],
                    "currency": os.getenv("MOEDA_LUCRO"),
                    "basebet": state["nextbet"],
                    "chance_low": int(os.getenv("ANALISE_RESULTADO_INICIAL_LOW")),
                    "chance_high": int(os.getenv("ANALISE_RESULTADO_FINAL_LOW")),
                    "game_side": os.getenv("POSICAO_LUCRO"),
                }

            if state["game_play_side"] == "high":
                betData = {
                    "game_mode": state["game_mode"],
                    "currency": os.getenv("MOEDA_LUCRO"),
                    "basebet": state["nextbet"],
                    "chance_low": int(os.getenv("ANALISE_RESULTADO_INICIAL_HIGH")),
                    "chance_high": int(os.getenv("ANALISE_RESULTADO_FINAL_HIGH")),
                    "game_side": os.getenv("POSICAO_LUCRO"),
                }

        print("===== DADOS DA JOGADA =====")
        print(Fore.YELLOW + f"Moeda : {betData['currency']}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Bet : {betData['basebet']}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Lado : {betData['game_side']}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Chance Low : {betData['chance_low']}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Chance High : {betData['chance_high']}" + Style.RESET_ALL)
        resultBet = makeBet(windice, betData)

        if resultBet:
            print(Fore.LIGHTGREEN_EX + "===== APOSTA =====" + Style.RESET_ALL)
            print(
                Fore.LIGHTGREEN_EX
                + f"Posição: {'Dentro' if os.getenv("POSICAO_LUCRO") == 'in' else 'Fora'} do intervalo"
                + Style.RESET_ALL
            )
            print(
                Fore.LIGHTGREEN_EX
                + f"Intervalo: {betData['chance_low']} - {betData['chance_high']}"
                + Style.RESET_ALL
            )
            state["bet_count"] += 1

            if state["game_play_side"] == "low":
                state["target_high_count"] += 1

                if resultBet["result"] >= int(
                    os.getenv("ANALISE_RESULTADO_INICIAL_HIGH")
                ) and resultBet["result"] <= int(
                    os.getenv("ANALISE_RESULTADO_FINAL_HIGH")
                ):
                    state["target_high_count"] = 0

            if state["game_play_side"] == "high":
                state["target_low_count"] += 1

                if resultBet["result"] >= int(
                    os.getenv("ANALISE_RESULTADO_INICIAL_LOW")
                ) and resultBet["result"] <= int(
                    os.getenv("ANALISE_RESULTADO_FINAL_LOW")
                ):
                    state["target_low_count"] = 0

            if resultBet["win"] != 0:
                print(
                    Fore.GREEN
                    + f"Você ganhou! Seu retorno é de {resultBet['win']}."
                    + Style.RESET_ALL
                )

                winsound.PlaySound("sound_win.wav", winsound.SND_ALIAS)

                state["game_mode"] = 1
                state["bet_count"] = 0
                state["win_count"] = 0
                state["lose_count"] = 0
                state["target_low_count"] = 0
                state["target_high_count"] = 0
                state["game_play_side"] = 0
                state["nextbet"] = float(os.getenv("BASEBET_ANALISE"))
                save_state(state)
                # return True
            else:

                state["lose_count"] += 1
                state["win_count"] = 0

                if state["lose_count"] >= int(os.getenv("REPETIDOR_EM_PERDA")):
                    print(Fore.MAGENTA + "Jogando com multiplicador!" + Style.RESET_ALL)
                    state["nextbet"] = resultBet["bet"] * float(
                        os.getenv("MULTIPLICADOR")
                    )

            print(Fore.LIGHTBLACK_EX + "===== CONTADORES =====" + Style.RESET_ALL)
            print(Fore.LIGHTBLACK_EX + f"ROLLS: {state["bet_count"]}" + Style.RESET_ALL)
            print(
                Fore.LIGHTBLACK_EX
                + f"WINCOUNT: {state["win_count"]} "
                + Style.RESET_ALL
            )
            print(
                Fore.LIGHTBLACK_EX
                + f"LOSECOUNT: {state["lose_count"]}"
                + Style.RESET_ALL
            )
            print(
                Fore.LIGHTBLUE_EX
                + f"NÚMERO SORTEADO: {resultBet['result']}"
                + Style.RESET_ALL
            )
            print(Fore.LIGHTGREEN_EX + "===== BETS =====" + Style.RESET_ALL)
            print(Fore.LIGHTGREEN_EX + f"Próximo: {state["nextbet"]}" + Style.RESET_ALL)
            save_state(state)


# Função principal
def main():
    # Carrega o estado inicial
    state = load_state()

    # Instancia a classe Windice com a chave da API
    windice = Windice(API, WINDICE_BASE_URL)
    bet_rolls = 0

    if int(os.getenv("QUANTIDADE_DE_JOGADAS")) > 0:
        bet_rolls = os.getenv("QUANTIDADE_DE_JOGADAS")

    bot(windice, int(bet_rolls), state)

    # Salva o estado final ao sair
    save_state(state)


if __name__ == "__main__":
    main()
