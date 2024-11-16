from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models.agendamento import Agendamento
from datetime import datetime, timedelta
from config.database import create_connection, close_connection


agendamento_bp = Blueprint('agendamento_bp', __name__)


@agendamento_bp.route('/get_available_times/<data_agendamento>', methods=['GET'])
@login_required
def get_available_times(data_agendamento):
    HORARIO_INICIO = 9  # 9 da manhã
    HORARIO_FIM = 18    # 18h
    LIMITE_POR_HORARIO = 2
    # Converte a data para o formato de datetime para consultas
    data = datetime.strptime(data_agendamento, '%Y-%m-%d')

    # Horários possíveis no dia, de 9h às 18h, em intervalos de uma hora
    horarios_possiveis = [f"{h:02}:00" for h in range(
        HORARIO_INICIO, HORARIO_FIM)]

    # Consulta agendamentos já existentes no dia (exemplo de consulta com SQL)
    query = """SELECT hora_agendamento, COUNT(*) as qtd_agendamentos
               FROM agendamento
               WHERE data_agendamento = %s
               GROUP BY hora_agendamento"""
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(query, (data,))
    agendamentos_existentes = cursor.fetchall()
    close_connection(connection)

    # Converte os horários ocupados para um dicionário para fácil acesso
    horarios_ocupados = {ag[0]: ag[1] for ag in agendamentos_existentes}

    # Filtra horários disponíveis
    horarios_disponiveis = [
        horario for horario in horarios_possiveis
        if horarios_ocupados.get(horario, 0) < LIMITE_POR_HORARIO
    ]

    return jsonify({'horarios_disponiveis': horarios_disponiveis})


@agendamento_bp.route('/submit_agendamento', methods=['POST'])
@login_required
def submit_agendamento():
    pet_id = request.form.get('pet')
    servico_id = request.form.get('servico')
    data_agendamento = request.form.get('data_agendamento')
    horario_agendamento = request.form.get('horario_agendamento')
    print(" Os pets são: ", pet_id, "<", servico_id,
          data_agendamento, horario_agendamento)
    print('pegou os dados')
    # Verifique se todos os campos estão preenchidos
    if not pet_id or not servico_id or not data_agendamento or not horario_agendamento:
        flash("Por favor, preencha todos os campos", "error")
        print("Por favor, preencha todos os campos", "error")
        # Redireciona para a página de agendamento
        return redirect(url_for('pet_bp.agendamento_pets'))

    # Crie o agendamento no banco de dados
    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO agendamento (pet_idPet, serviço_id, data_agendamento, hora_agendamento, colaboradores_cpf)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (pet_id, servico_id, data_agendamento,
                  horario_agendamento, current_user.cpf_cliente)

        cursor.execute(query, values)
        connection.commit()
        print("Agendamento realizado com sucesso!", "success")

        flash("Agendamento realizado com sucesso!", "success")
        # Redireciona para a tela inicial
        return redirect(url_for('cliente_bp.tela_inicial'))

    except Exception as e:
        flash(f"Erro ao agendar: {str(e)}", "error")
        print(f"Erro ao agendar: {str(e)}", "error")

        # Redireciona de volta em caso de erro
        return redirect(url_for('pet_bp.agendamento_pets'))

    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


@agendamento_bp.route('/meus_agendamentos')
@login_required
def meus_agendamentos():
    # Pega os agendamentos do banco
    agendamentos = Agendamento.get_agendamentos_from_db(
        current_user.cpf_cliente)
    return render_template('meusagendamentos.html', agendamentos=agendamentos)


@agendamento_bp.route('/apagar_agendamento/<int:agendamento_id>', methods=['GET', 'POST'])
def apagar_agendamento(agendamento_id):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "DELETE FROM agendamento WHERE id_agendamento = %s", (agendamento_id,))
        connection.commit()
        flash("Agendamento deletado com sucesso!", "success")
        print("Agendamento deletado com sucesso!", "success")
    except Exception as e:
        connection.rollback()
        flash("Erro ao deletar o agendamento.", "danger")
        print(f"Erro ao deletar o agendamento.{e}", "danger")
    finally:
        close_connection(connection)

    return redirect(url_for('agendamento_bp.meus_agendamentos'))
