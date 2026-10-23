# Livro de códigos: enquadramento da IA (`ia_enquadramento.csv`)

**Unidade:** a frase do entrevistado que menciona a IA, ou que se refere a ela por pronome. A extração está em `data/ia_mencoes.csv`, feita por `scripts/ia_enquadramento.py extrair`.

Cada frase recebe um código principal. Recebe também um secundário quando combina dois enquadramentos de forma clara.

| código | polo | quando usar | exemplos (parafraseados) |
|---|---|---|---|
| `instrumento` | coisa | A IA é meio ou objeto da ação humana: é usada, alimentada, configurada, paga, comparada como produto, ou nomeada como ferramenta, recurso ou acessório. Também quando a IA é sujeito de um verbo operacional, como gerar, transcrever, resumir ou traduzir. | "uso o GPT pra revisar"; "jogo os documentos lá"; "ela transcreve a reunião" |
| `negacao` | coisa | Tomada de posição explícita que nega à IA mente, pessoa ou relação ("não é uma pessoa", "é só máquina", "é matemática", "não tem personalidade", "me forço a lembrar que é algoritmo"). Inclui a recusa declarada de trato social ("não dou bom dia", "não trato como amiga"). | "a IA não é uma pessoa"; "sou do prompt direto, não dou bom dia" |
| `agente` | alguém | A IA é sujeito com mente, voz, intenção ou iniciativa: pensa, entende, sabe, sugere, erra, mente, "me ajuda", "criou pra mim", pergunta, aprende. Inclui a fala relatada ("o ChatGPT falou: …"), a atribuição de personalidade ou de traços e a IA como ator que age sobre o mundo ("a IA vai substituir…"; a nota diz "macro"). | "ele me perguntou se era isso"; "a IA erra"; "o Claude me alertou" |
| `interlocutor` | alguém | Relação social com a IA: cumprimentar, agradecer, pedir por favor, ser educado ou grosseiro, conversar ou desabafar. Inclui tratar a IA como papel humano (estagiário, assistente, funcionário, terapeuta, amigo, colega) ou compará-la a ele, e apelidos ou afetos dirigidos a ela ("chatinho", raiva, "ele me conhece"). | "mandei bom dia, chatinho"; "ela faz o que o estagiário fazia" |
| `neutro` | — | Menciona a IA sem enquadrá-la: o tema, o mercado, estudar IA, listas de ferramentas. | "a IA tá em todo lugar" |
| `nao_ia` | — | A frase não se refere à IA: o pronome ou o termo aponta para outra coisa (uma pessoa, um agente humano, uma máquina física). | — |

## Regras de decisão

1. **A tomada de posição vence.** Uma frase que diz o que a IA é ou não é recebe `negacao` (se nega mente ou pessoa) ou `agente` (se atribui mente ou personalidade), mesmo que fale também de uso.
2. **`interlocutor` × `agente`:** a conduta social do usuário com a IA, ou um papel humano, é `interlocutor`. A ação mental ou comunicativa da própria IA é `agente`.
3. **`agente` × `instrumento`:** verbos mentais, comunicativos ou de intenção são `agente`. Verbos de saída ou operação são `instrumento`.
4. **Voz:** a coluna `proprio` vale 0 quando a frase relata o enquadramento de terceiros ("as pessoas acham que ela pensa"). A análise de oscilação usa só as frases com `proprio = 1`.
5. **Na dúvida entre um polo e `neutro`, fica `neutro`.** A medida é conservadora: só conta como oscilação o que está claro.

## Polos usados na análise

- **coisa:** `instrumento`, `negacao`.
- **alguém:** `agente`, `interlocutor`.

A oscilação é a alternância entre os polos, na ordem do tempo, dentro de uma entrevista.

## Referências

- Epley, N., Waytz, A., & Cacioppo, J. T. (2007). On seeing human: A three-factor theory of anthropomorphism. *Psychological Review, 114*(4), 864–886.
- Mick, D. G., & Fournier, S. (1998). Paradoxes of technology: Consumer cognizance, emotions, and coping strategies. *Journal of Consumer Research, 25*(2), 123–143.
- Nass, C., & Moon, Y. (2000). Machines and mindlessness: Social responses to computers. *Journal of Social Issues, 56*(1), 81–103.
- Otnes, C., Lowrey, T. M., & Shrum, L. J. (1997). Toward an understanding of consumer ambivalence. *Journal of Consumer Research, 24*(1), 80–93.
