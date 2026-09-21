import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import os
from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseManager")

PONTOS_POR_FORMULARIO=10

class SaldoInsuficiente(Exception):
    pass

class SemEstoque(Exception):
    pass

class FormulariosIncompletos(Exception):
    pass

class JaResgatouBrindePadrao(Exception):
    pass

class DatabaseManager:

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        try:
            self.engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
            logger.info("Engine do Banco de Dados inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao criar o Engine do Banco de Dados: {str(e)}")
            raise e

    def id_public_existe(self, id_public: str) -> bool:
        query = text("SELECT 1 FROM users WHERE id_public = :id_public")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"id_public": id_public}).fetchone()
        return resultado is not None    

    def buscar_por_telefone(self, numero_cel: str) -> dict | None:
        query = text("SELECT * FROM users WHERE numero_cel = :numero_cel")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"numero_cel": numero_cel}).mappings().fetchone()
        return dict(resultado) if resultado else None

    def buscar_por_email(self, email: str) -> dict | None:
        query = text("SELECT * FROM users WHERE email = :email")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"email": email}).mappings().fetchone()
        return dict(resultado) if resultado else None

    def inserir_usuario(self, nome: str, numero_cel: str, email: str, id_public: str, aceite_marketing: bool) -> dict | None:
        query = text("""
            INSERT INTO users (nome, numero_cel, email, id_public, aceite_marketing)
            VALUES (:nome, :numero_cel, :email, :id_public, :aceite_marketing)
            RETURNING *
        """)
        try:
            with self.engine.begin() as conn:
                resultado = conn.execute(
                    query,
                    {"nome": nome, "numero_cel": numero_cel, "email": email, "id_public": id_public, "aceite_marketing": aceite_marketing},
                ).mappings().fetchone()
            logger.info(f"Usuário {id_public} inserido com sucesso.")
            return dict(resultado)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao inserir usuário: {e}")
            return None

    def buscar_por_id_public(self, id_public: str) -> dict | None:
        query = text("SELECT * FROM users WHERE id_public = :id_public")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"id_public": id_public}).mappings().fetchone()
        return dict(resultado) if resultado else None


    def buscar_loja_por_codigo(self, codigo_publico: str) -> dict | None:
        query = text("SELECT * FROM lojas WHERE codigo_publico = :codigo_publico")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"codigo_publico": codigo_publico}).mappings().fetchone()
        return dict(resultado) if resultado else None

    
    def codigo_loja_existe(self, codigo: str) -> bool:
        query = text("SELECT 1 FROM lojas WHERE codigo_publico = :codigo")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"codigo": codigo}).fetchone()
        return resultado is not None

    def inserir_loja(self, codigo_publico: str, nome: str, pontos_base: int) -> dict | None:
        query = text("""
            INSERT INTO lojas (codigo_publico, nome, pontos_base)
            VALUES (:codigo_publico, :nome, :pontos_base)
            RETURNING *
        """)
        try:
            with self.engine.begin() as conn:
                resultado = conn.execute(
                    query,
                    {"codigo_publico": codigo_publico, "nome": nome, "pontos_base": pontos_base},
                ).mappings().fetchone()
            logger.info(f"Loja {nome} inserida com sucesso.")
            return dict(resultado)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao inserir loja: {e}")
            return None

    def registrar_pontuacao(self, visitante_id: int, loja_id: int, pontos: int) -> str:
        query_pontuacao = text("""
            INSERT INTO pontuacoes (visitante_id, loja_id, pontos)
            VALUES (:visitante_id, :loja_id, :pontos)
        """)
        query_saldo = text("""
            UPDATE users SET pontos_atuais = pontos_atuais + :pontos WHERE id = :visitante_id
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(query_pontuacao, {"visitante_id": visitante_id, "loja_id": loja_id, "pontos": pontos})
                conn.execute(query_saldo, {"visitante_id": visitante_id, "pontos": pontos})
            logger.info(f"Pontuação registrada: visitante {visitante_id} na loja {loja_id}.")
            return "ok"
        except IntegrityError:
            logger.warning(f"Tentativa de pontuação duplicada: visitante {visitante_id} na loja {loja_id}.")
            return "duplicado"
        except SQLAlchemyError as e:
            logger.error(f"Erro ao registrar pontuação: {e}")
            return "erro"

    def _somar_pontos(self, conn, visitante_id: int, pontos: int):
        """Soma pontos no saldo do usuário. Só funciona chamado de DENTRO de uma
        transação já aberta (por isso recebe 'conn' pronto, não abre conexão nova)."""
        query = text("UPDATE users SET pontos_atuais = pontos_atuais + :pontos WHERE id = :visitante_id")
        conn.execute(query, {"visitante_id": visitante_id, "pontos": pontos})

    def registrar_entrada_juquita(self, visitante_id: int, ficou_sabendo_onde: str) -> str:
        """Retorna 'ok', 'duplicado' ou 'erro'."""
        query = text("""
            INSERT INTO interacoes_entrada_juquita (visitante_id, ficou_sabendo_onde)
            VALUES (:visitante_id, :ficou_sabendo_onde)
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(query, {
                    "visitante_id": visitante_id,
                    "ficou_sabendo_onde": ficou_sabendo_onde
                })
                self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
            logger.info(f"Entrada Juquita registrado para visitante {visitante_id}.")
            return "ok"
        except IntegrityError:
            logger.warning(f"Visitante {visitante_id} já respondeu à Entrada Juquita.")
            return "duplicado"
        except SQLAlchemyError as e:
            logger.error(f"Erro ao registrar Entrada Juquita: {e}")
            return "erro"

    def registrar_vip_lounge(self, visitante_id: int, prioridade: str, quantas_sacolas: str) -> str:
            """Retorna 'ok', 'duplicado' ou 'erro'."""
            query = text("""
                INSERT INTO interacoes_lounge_vip (visitante_id, prioridade, quantas_sacolas)
                VALUES (:visitante_id, :prioridade, :quantas_sacolas)
            """)
            try:
                with self.engine.begin() as conn:
                    conn.execute(query, {
                        "visitante_id": visitante_id,
                        "prioridade": prioridade,
                        "quantas_sacolas": quantas_sacolas,
                    })
                    self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
                logger.info(f"Vip Lounge registrado para visitante {visitante_id}.")
                return "ok"
            except IntegrityError:
                logger.warning(f"Visitante {visitante_id} já respondeu o Vip Lounge.")
                return "duplicado"
            except SQLAlchemyError as e:
                logger.error(f"Erro ao registrar Vip Lounge: {e}")
                return "erro"

    def registrar_acao_guerrilha(self, visitante_id: int, oque_trouxe: str, regiao: str) -> str:
        """Retorna 'ok', 'duplicado' ou 'erro'."""
        query = text("""
            INSERT INTO interacoes_acao_guerrilha (visitante_id, oque_trouxe, regiao)
            VALUES (:visitante_id, :oque_trouxe, :regiao)
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(query, {
                    "visitante_id": visitante_id,
                    "oque_trouxe": oque_trouxe,
                    "regiao": regiao
                })
                #self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
            logger.info(f"Ação Guerrilha registrada para visitante {visitante_id}.")
            return "ok"
        except IntegrityError:
            logger.warning(f"Visitante {visitante_id} já respondeu a Ação Guerrilha.")
            return "duplicado"
        except SQLAlchemyError as e:
            logger.error(f"Erro ao registrar Ação Guerrilha: {e}")
            return "erro"

        

    def registrar_tudao(
        self,
        visitante_id: int,
        quem_e_voce: str,
        foco_principal: str,
        regiao_origem: str,
        como_veio_exagerado: str,
        tempo_ate_chegar: str,
        ritmo_do_item: str,
        faixa_idade: str,
        como_ficou_sabendo: str,
        maior_garimpo: str,
        marca_favorita: str,
        prioridade_lounge_vip: str,
        quantidade_sacolas: str,
        faixa_renda: str,
        valor_gasto: str,
        companhia_role: str,
        melhor_dia: str,
        forma_pagamento: str,
        nota_recomendacao: int,
        maior_destaque: str,
        proxima_edicao_sp: str,
        feedback_geral: str
    ) -> str:

        """Retorna 'ok' ou 'erro'."""

        query = text("""
            INSERT INTO interacoes_tudao (
                visitante_id,
                quem_e_voce,
                foco_principal,
                regiao_origem,
                como_veio_exagerado,
                tempo_ate_chegar,
                ritmo_do_item,
                faixa_idade,
                como_ficou_sabendo,
                maior_garimpo,
                marca_favorita,
                prioridade_lounge_vip,
                quantidade_sacolas,
                faixa_renda,
                valor_gasto,
                companhia_role,
                melhor_dia,
                forma_pagamento,
                nota_recomendacao,
                maior_destaque,
                proxima_edicao_sp,
                feedback_geral
            )
            VALUES (
                :visitante_id,
                :quem_e_voce,
                :foco_principal,
                :regiao_origem,
                :como_veio_exagerado,
                :tempo_ate_chegar,
                :ritmo_do_item,
                :faixa_idade,
                :como_ficou_sabendo,
                :maior_garimpo,
                :marca_favorita,
                :prioridade_lounge_vip,
                :quantidade_sacolas,
                :faixa_renda,
                :valor_gasto,
                :companhia_role,
                :melhor_dia,
                :forma_pagamento,
                :nota_recomendacao,
                :maior_destaque,
                :proxima_edicao_sp,
                :feedback_geral
            )
        """)

        try:
            with self.engine.begin() as conn:
                conn.execute(query, {
                    "visitante_id": visitante_id,
                    "quem_e_voce": quem_e_voce,
                    "foco_principal": foco_principal,
                    "regiao_origem": regiao_origem,
                    "como_veio_exagerado": como_veio_exagerado,
                    "tempo_ate_chegar": tempo_ate_chegar,
                    "ritmo_do_item": ritmo_do_item,
                    "faixa_idade": faixa_idade,
                    "como_ficou_sabendo": como_ficou_sabendo,
                    "maior_garimpo": maior_garimpo,
                    "marca_favorita": marca_favorita,
                    "prioridade_lounge_vip": prioridade_lounge_vip,
                    "quantidade_sacolas": quantidade_sacolas,
                    "faixa_renda": faixa_renda,
                    "valor_gasto": valor_gasto,
                    "companhia_role": companhia_role,
                    "melhor_dia": melhor_dia,
                    "forma_pagamento": forma_pagamento,
                    "nota_recomendacao": nota_recomendacao,
                    "maior_destaque": maior_destaque,
                    "proxima_edicao_sp": proxima_edicao_sp,
                    "feedback_geral": feedback_geral
                })
                logger.info(f"Formulário Tudão registrado para visitante {visitante_id}.")
                return "ok"
        except IntegrityError:
            logger.warning(f"Visitante {visitante_id} já respondeu ao formulário Tudão.")
            return "duplicado"
        except SQLAlchemyError as e:
            logger.error(f"Erro ao registrar formulário Tudão: {e}")
            return "erro"

            

    def registrar_boas_vindas(self, visitante_id: int, regiao: str) -> str:
            """Retorna 'ok', 'duplicado' ou 'erro'."""
            query = text("""
                INSERT INTO interacoes_boas_vindas (visitante_id, regiao)
                VALUES (:visitante_id, :regiao)
            """)
            try:
                with self.engine.begin() as conn:
                    conn.execute(query, {
                        "visitante_id": visitante_id,
                        "regiao": regiao
                    })
                    self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
                logger.info(f"Boas Vindas registrada para visitante {visitante_id}.")
                return "ok"
            except IntegrityError:
                logger.warning(f"Visitante {visitante_id} já respondeu às Boas Vindas.")
                return "duplicado"
            except SQLAlchemyError as e:
                logger.error(f"Erro ao registrar Boas Vindas: {e}")
                return "erro"

    def registrar_estacionamento(self, visitante_id: int, como_veio: str, quanto_tempo: str) -> str:
                """Retorna 'ok', 'duplicado' ou 'erro'."""
                query = text("""
                    INSERT INTO interacoes_estacionamento (visitante_id, como_veio, quanto_tempo)
                    VALUES (:visitante_id, :como_veio, :quanto_tempo)
                """)
                try:
                    with self.engine.begin() as conn:
                        conn.execute(query, {
                            "visitante_id": visitante_id,
                            "como_veio": como_veio,
                            "quanto_tempo": quanto_tempo
                        })
                        self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
                    logger.info(f"Estacionamento registrada para visitante {visitante_id}.")
                    return "ok"
                except IntegrityError:
                    logger.warning(f"Visitante {visitante_id} já respondeu ao Estacionamento.")
                    return "duplicado"
                except SQLAlchemyError as e:
                    logger.error(f"Erro ao registrar Estacionamento: {e}")
                    return "erro"

    def registrar_cenografia(self, visitante_id: int, oque_mais_garimpou: str, qual_marca_deixou_louco: str) -> str:
                    """Retorna 'ok', 'duplicado' ou 'erro'."""
                    query = text("""
                        INSERT INTO interacoes_cenografia (visitante_id, oque_mais_garimpou, qual_marca_deixou_louco)
                        VALUES (:visitante_id, :oque_mais_garimpou, :qual_marca_deixou_louco)
                    """)
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(query, {
                                "visitante_id": visitante_id,
                                "oque_mais_garimpou": oque_mais_garimpou,
                                "qual_marca_deixou_louco": qual_marca_deixou_louco
                            })
                            self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
                        logger.info(f"Cenografia registrada para visitante {visitante_id}.")
                        return "ok"
                    except IntegrityError:
                        logger.warning(f"Visitante {visitante_id} já respondeu ao Cenografia.")
                        return "duplicado"
                    except SQLAlchemyError as e:
                        logger.error(f"Erro ao registrar Cenografia: {e}")
                        return "erro"

    def registrar_saida_juquita(self, visitante_id: int, qual_renda: str, quanto_pretende_gastar: str, com_quem_veio: str) -> str:
            """Retorna 'ok', 'duplicado' ou 'erro'."""
            query = text("""
                INSERT INTO interacoes_saida_juquita (visitante_id, qual_renda, quanto_pretende_gastar, com_quem_veio)
                VALUES (:visitante_id, :qual_renda, :quanto_pretende_gastar, :com_quem_veio)
            """)
            try:
                with self.engine.begin() as conn:
                    conn.execute(query, {
                        "visitante_id": visitante_id,
                        "qual_renda": qual_renda,
                        "quanto_pretende_gastar": quanto_pretende_gastar,
                        "com_quem_veio": com_quem_veio
                    })
                    self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
                logger.info(f"Saída Juquita registrado para visitante {visitante_id}.")
                return "ok"
            except IntegrityError:
                logger.warning(f"Visitante {visitante_id} já respondeu à Saída Juquita.")
                return "duplicado"
            except SQLAlchemyError as e:
                logger.error(f"Erro ao registrar Saída Juquita: {e}")
                return "erro"

    def registrar_dentro_lojas(self, visitante_id: int, melhor_dia: str, forma_pagamento: str) -> str:
                """Retorna 'ok', 'duplicado' ou 'erro'."""
                query = text("""
                    INSERT INTO interacoes_dentro_lojas (visitante_id, melhor_dia, forma_pagamento)
                    VALUES (:visitante_id, :melhor_dia, :forma_pagamento)
                """)
                try:
                    with self.engine.begin() as conn:
                        conn.execute(query, {
                            "visitante_id": visitante_id,
                            "melhor_dia": melhor_dia,
                            "forma_pagamento": forma_pagamento
                        })
                        self._somar_pontos(conn, visitante_id, PONTOS_POR_FORMULARIO)
                    logger.info(f"Lojas registrado para visitante {visitante_id}.")
                    return "ok"
                except IntegrityError:
                    logger.warning(f"Visitante {visitante_id} já respondeu à Lojas.")
                    return "duplicado"
                except SQLAlchemyError as e:
                    logger.error(f"Erro ao registrar Lojas: {e}")
                    return "erro"

    def registrar_saida_nps(self, visitante_id: int, quanto_recomenda: int, maior_destaque: str, te_vejo_proxima_edicao: str, feedback: str) -> str:
                    """Retorna 'ok', 'duplicado' ou 'erro'."""
                    query = text("""
                        INSERT INTO interacoes_saida_nps (visitante_id, quanto_recomenda, maior_destaque, te_vejo_proxima_edicao, feedback)
                        VALUES (:visitante_id, :quanto_recomenda, :maior_destaque, :te_vejo_proxima_edicao, :feedback)
                    """)
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(query, {
                                "visitante_id": visitante_id,
                                "quanto_recomenda": quanto_recomenda,
                                "maior_destaque": maior_destaque,
                                "te_vejo_proxima_edicao": te_vejo_proxima_edicao,
                                "feedback": feedback
                            })
                        logger.info(f"NPS registrado para visitante {visitante_id}.")
                        return "ok"
                    except IntegrityError:
                        logger.warning(f"Visitante {visitante_id} já respondeu ao NPS.")
                        return "duplicado"
                    except SQLAlchemyError as e:
                        logger.error(f"Erro ao registrar NPS: {e}")
                        return "erro"

    def buscar_formularios_respondidos(self, visitante_id: int) -> dict[str, bool]:
        query = text("""
            SELECT
                EXISTS(SELECT 1 FROM interacoes_lounge_vip WHERE visitante_id = :id) AS lounge_vip,
                EXISTS(SELECT 1 FROM interacoes_entrada_juquita WHERE visitante_id = :id) AS entrada_juquita,
                EXISTS(SELECT 1 FROM interacoes_acao_guerrilha WHERE visitante_id = :id) AS acao_guerrilha,
                EXISTS(SELECT 1 FROM interacoes_boas_vindas WHERE visitante_id = :id) AS boas_vindas,
                EXISTS(SELECT 1 FROM interacoes_cenografia WHERE visitante_id = :id) AS cenografia,
                EXISTS(SELECT 1 FROM interacoes_dentro_lojas WHERE visitante_id = :id) AS dentro_lojas,
                EXISTS(SELECT 1 FROM interacoes_estacionamento WHERE visitante_id = :id) AS estacionamento,
                EXISTS(SELECT 1 FROM interacoes_saida_juquita WHERE visitante_id = :id) AS saida_juquita,
                EXISTS(SELECT 1 FROM interacoes_saida_nps WHERE visitante_id = :id) AS saida_nps,
                EXISTS(SELECT 1 FROM interacoes_tudao WHERE visitante_id = :id) AS tudao
        """)
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"id": visitante_id}).mappings().fetchone()
        return {
            "Entrada Juquita": resultado["entrada_juquita"],
            "Lounge VIP": resultado["lounge_vip"],
            "Acao Guerrilha": resultado["acao_guerrilha"],
            "Boas Vindas": resultado["boas_vindas"],
            "Cenografia": resultado["cenografia"],
            "Dentro Lojas": resultado["dentro_lojas"],
            "Corredor 2º piso": resultado["estacionamento"],
            "Rampa 2º piso": resultado["saida_juquita"],
            "NPS": resultado["saida_nps"],
            "Tudao": resultado["tudao"],
        }

    def verificar_cadastro_periodo(self, visitante_id: int) -> bool:
            query = text("""
                SELECT EXISTS(SELECT 1 FROM users WHERE id = :visitante_id AND DATE(created_at) BETWEEN '2026-09-19' AND '2026-09-22')
            """)
            with self.engine.connect() as conn:
                resultado = conn.execute(query, {"visitante_id": visitante_id}).fetchone()
            return resultado[0]

    def buscar_resumo_pontuacao_usuario(self, id_public: str) -> dict | None:
        query_usuario = text("""
            SELECT
                id,
                nome,
                pontos_atuais
            FROM users
            WHERE id_public = :id_public
        """)

        query_lojas = text("""
            SELECT
                l.nome AS loja_nome,
                SUM(p.pontos) AS pontos
            FROM pontuacoes p
            JOIN lojas l
                ON l.id = p.loja_id
            JOIN users u
                ON u.id = p.visitante_id
            WHERE u.id_public = :id_public
            GROUP BY l.id, l.nome
            ORDER BY l.nome
        """)

        query_resgates = text("""
            SELECT
                b.nome AS brinde_nome,
                r.pontos_debitados
            FROM resgates r
            JOIN brindes b
                ON b.id = r.brinde_id
            JOIN users u
                ON u.id = r.visitante_id
            WHERE u.id_public = :id_public
            ORDER BY r.id DESC
        """)

        with self.engine.connect() as conn:
            usuario = conn.execute(
                query_usuario,
                {"id_public": id_public}
            ).mappings().fetchone()

            if usuario is None:
                return None

            lojas = conn.execute(
                query_lojas,
                {"id_public": id_public}
            ).mappings().fetchall()

            resgates = conn.execute(
                query_resgates,
                {"id_public": id_public}
            ).mappings().fetchall()

        formularios = self.buscar_formularios_respondidos(usuario["id"])

        return {
            "usuario_id": usuario["id"],
            "usuario_nome": usuario["nome"],
            "pontos_atuais": usuario["pontos_atuais"],
            "lojas": [
                {
                    "loja": loja["loja_nome"],
                    "pontos": loja["pontos"],
                }
                for loja in lojas
            ],
            "resgates": [
                {
                    "brinde": resgate["brinde_nome"],
                    "pontos": resgate["pontos_debitados"],
                }
                for resgate in resgates
            ],
            "formularios": formularios
        }

    def inserir_brinde(self, nome: str, custo_pontos: int, estoque: int, tipo: str) -> dict | None:
        query = text("""
            INSERT INTO brindes (nome, custo_pontos, estoque, tipo)
            VALUES (:nome, :custo_pontos, :estoque, :tipo)
            RETURNING *
        """)
        try:
            with self.engine.begin() as conn:
                resultado = conn.execute(query, {
                    "nome": nome,
                    "custo_pontos": custo_pontos,
                    "estoque": estoque,
                    "tipo": tipo
                }).mappings().fetchone()
            return dict(resultado)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao inserir brinde: {e}")
            return None

    def buscar_brindes_disponiveis(self) -> list[dict]:
        query = text("SELECT * FROM brindes WHERE estoque > 0 ORDER BY nome")
        with self.engine.connect() as conn:
            resultados = conn.execute(query).mappings().fetchall()
        return [dict(row) for row in resultados]

    def buscar_brindes_disponiveis_por_visitante(self, pontos: int, visitante_id: int) -> list[dict]:
            query = text("""
                select 
                    * 
                from 
                    brindes 
                where 
                    estoque > 0 
                and custo_pontos <= :pontos and tipo = 'padrao'

                union

                select 
                    *
                from
                    brindes
                where
                    tipo = 'gratis'
                and (SELECT
                        EXISTS(SELECT 1 FROM interacoes_lounge_vip WHERE visitante_id = :visitante_id) AND 
                        EXISTS(SELECT 1 FROM interacoes_entrada_juquita WHERE visitante_id = :visitante_id) AND
                        EXISTS(SELECT 1 FROM interacoes_acao_guerrilha WHERE visitante_id = :visitante_id) AND
                        EXISTS(SELECT 1 FROM interacoes_boas_vindas WHERE visitante_id = :visitante_id) AND
                        EXISTS(SELECT 1 FROM interacoes_cenografia WHERE visitante_id = :visitante_id) AND
                        EXISTS(SELECT 1 FROM interacoes_dentro_lojas WHERE visitante_id = :visitante_id) AND 
                        EXISTS(SELECT 1 FROM interacoes_estacionamento WHERE visitante_id = :visitante_id) AND
                        EXISTS(SELECT 1 FROM interacoes_saida_juquita WHERE visitante_id = :visitante_id) AND
                        EXISTS(SELECT 1 FROM interacoes_saida_nps WHERE visitante_id = :visitante_id)) = true

                union

                select 
                    * 
                from 
                    brindes 
                where 
                    tipo = 'periodo'
                and exists (
                    SELECT 1 FROM users WHERE id = :visitante_id AND DATE(created_at) BETWEEN '2026-09-19' AND '2026-09-22'
                )
                order by nome
            """)

            with self.engine.connect() as conn:
                resultados = conn.execute(query, {"pontos": pontos, "visitante_id": visitante_id}).mappings().fetchall()
            return [dict(row) for row in resultados]

    def listar_brindes(self) -> list[dict]:
        query = text("SELECT * FROM brindes ORDER BY custo_pontos")
        with self.engine.connect() as conn:
            resultados = conn.execute(query).mappings().fetchall()
        return [dict(row) for row in resultados]

    def buscar_brinde(self, brinde_id: int) -> dict | None:
        query = text("SELECT * FROM brindes WHERE id = :id")
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"id": brinde_id}).mappings().fetchone()
        return dict(resultado) if resultado else None

    def resgatar_brinde(self, visitante_id: int, brinde_id: int, custo_pontos: int, tipo: str) -> str:
        """Retorna 'ok', 'saldo_insuficiente', 'sem_estoque', 'formularios_incompletos', 'cadastro_fora_periodo',
        'ja_resgatou_padrao', 'duplicado' ou 'erro'."""

        if tipo == "gratis":
            formularios = self.buscar_formularios_respondidos(visitante_id)
            if not all(formularios.values()):
                return "formularios_incompletos"

        if tipo == "periodo":
            #formularios = self.buscar_formularios_respondidos(visitante_id)
            cadastrou_periodo = self.verificar_cadastro_periodo(visitante_id)

            if not cadastrou_periodo:
                 return "cadastro_fora_periodo"

        #if tipo == "padrao_periodo":
        #        cadastrou_periodo = self.verificar_cadastro_periodo(visitante_id)
    
        #query_ja_resgatou_padrao = text("""
        #    SELECT 1 FROM resgates r
        #    JOIN brindes b ON b.id = r.brinde_id
        #    WHERE r.visitante_id = :visitante_id AND b.tipo = 'padrao'
        #""")

        query_ja_resgatou_periodo = text("""
            SELECT 1 FROM resgates r
            JOIN brindes b ON b.id = r.brinde_id
            WHERE r.visitante_id = :visitante_id AND b.tipo = 'periodo'
        """)

        query_debita_saldo = text("""
            UPDATE users SET pontos_atuais = pontos_atuais - :custo
            WHERE id = :visitante_id AND pontos_atuais >= :custo
            RETURNING id
        """)
        query_debita_estoque = text("""
            UPDATE brindes SET estoque = estoque - 1
            WHERE id = :brinde_id AND estoque > 0
            RETURNING id
        """)
        query_log = text("""
            INSERT INTO resgates (visitante_id, brinde_id, pontos_debitados)
            VALUES (:visitante_id, :brinde_id, :custo)
        """)

        try:
            with self.engine.begin() as conn:
                #if tipo == "padrao":
                #    if conn.execute(query_ja_resgatou_padrao, {"visitante_id": visitante_id}).fetchone() is not None:
                #        raise JaResgatouBrindePadrao()

                if tipo == "periodo":
                    if conn.execute(query_ja_resgatou_periodo, {"visitante_id": visitante_id}).fetchone() is not None:
                        raise JaResgatouBrindePadrao()
                if conn.execute(query_debita_saldo, {"visitante_id": visitante_id, "custo": custo_pontos}).fetchone() is None:
                    raise SaldoInsuficiente()
                if conn.execute(query_debita_estoque, {"brinde_id": brinde_id}).fetchone() is None:
                    raise SemEstoque()
                conn.execute(query_log, {"visitante_id": visitante_id, "brinde_id": brinde_id, "custo": custo_pontos})
            return "ok"
        except JaResgatouBrindePadrao:
            return "ja_resgatou_padrao"
        except SaldoInsuficiente:
            return "saldo_insuficiente"
        except SemEstoque:
            return "sem_estoque"
        except IntegrityError:
            return "duplicado"
        except SQLAlchemyError as e:
            logger.error(f"Erro ao resgatar brinde: {e}")
            return "erro"

    def buscar_total_visitantes(self) -> int:
            query = text("SELECT count(*) FROM users")
            with self.engine.connect() as conn:
                resultado = conn.execute(query).scalar_one()
            return int(resultado)

    def buscar_total_lojas(self) -> int:
                query = text("SELECT count(*) FROM lojas")
                with self.engine.connect() as conn:
                    resultado = conn.execute(query).scalar_one()
                return int(resultado)

    def buscar_total_brindes(self) -> int:
                    query = text("SELECT count(*) FROM brindes")
                    with self.engine.connect() as conn:
                        resultado = conn.execute(query).scalar_one()
                    return int(resultado)

    def buscar_visitante(self, nome: str, data: str) -> list[dict] | None:
        nome = nome.strip()
        data = data.strip()

        query_sql = """
                    SELECT
                        nome,
                        numero_cel,
                        email,
                        id_public,
                        pontos_atuais,
                        aceite_marketing,
                        TO_CHAR(created_at, 'DD/MM/YYYY') AS created_at
                    FROM users
                    WHERE 1=1
                """

        params = {}

        if nome:
            query_sql += """
                AND (
                    UPPER(nome) LIKE UPPER('%' || :nome || '%')
                    OR numero_cel = :nome
                    OR email = :nome
                    OR id_public = :nome
                )
            """
            params["nome"] = nome

        if data:
            query_sql += """
                AND DATE(created_at) = :data
            """
            params["data"] = data

        query = text(query_sql)
        
        with self.engine.connect() as conn:
            resultado = conn.execute(query, params).mappings().fetchall()
        return [dict(row) for row in resultado]

    def buscar_loja(self, nome: str) -> list[dict] | None:
        query = text("""
                        SELECT codigo_publico, nome, pontos_base, to_char(created_at, 'DD/MM/YYYY') created_at
                        FROM lojas WHERE upper(nome) like upper('%' || :nome || '%')
                        OR codigo_publico = :nome
                    """)
        with self.engine.connect() as conn:
            resultado = conn.execute(query, {"nome": nome}).mappings().fetchall()
        return [dict(row) for row in resultado]    

load_dotenv()
db = DatabaseManager(connection_string=os.getenv("db_uri"))
