// ─── Processador: ExecuteScript (Groovy) ───────────────────────────────────
// Lê o FlowFile JSON recebido, identifica se o documento é CPF ou PJ (CNPJ)
// e adiciona um atributo "tipo_cliente" = "PF" ou "PJ"
// ────────────────────────────────────────────────────────────────────────────

import org.apache.commons.io.IOUtils
import java.nio.charset.StandardCharsets
import groovy.json.JsonSlurper

def flowFile = session.get()
if (!flowFile) return

def conteudo = ""
session.read(flowFile, { inputStream ->
    conteudo = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
} as InputStreamCallback)

def slurper = new JsonSlurper()
def dados = slurper.parseText(conteudo)

def documento = dados.documento?.replaceAll("[^0-9]", "") ?: ""

String tipo
if (documento.length() == 11) {
    tipo = "PF"   // CPF tem 11 dígitos
} else if (documento.length() == 14) {
    tipo = "PJ"   // CNPJ tem 14 dígitos
} else {
    tipo = "DESCONHECIDO"
}

// Adiciona atributos ao FlowFile para uso nos roteamentos seguintes
flowFile = session.putAttribute(flowFile, "tipo_cliente", tipo)
flowFile = session.putAttribute(flowFile, "nome_cliente", dados.nome ?: "")
flowFile = session.putAttribute(flowFile, "documento_cliente", dados.documento ?: "")
flowFile = session.putAttribute(flowFile, "demanda_cliente", dados.demanda ?: "")

session.transfer(flowFile, REL_SUCCESS)
