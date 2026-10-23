# Dicionário de self e identidade (`self_identidade.csv`)

Não existe dicionário validado de "self" ou "identidade" para análise de texto, nem em inglês nem em português (busca de 23/10/2026). O recurso consagrado é a categoria de pronomes de 1ª pessoa do singular do LIWC, que tem versão brasileira. Por isso o dicionário foi montado por categorias tiradas da literatura, e os aspectos do self seguem a teoria de Gallagher (2013).

Cada linha tem um padrão (expressão regular, sem diferenciar maiúsculas) aplicado às frases dos entrevistados. Algumas linhas trazem também um padrão de exclusão. A coluna `semente` diz se o termo serve de ponto de partida para a vizinhança (1) ou se só é medido (0).

| categoria | o que capta | base |
|---|---|---|
| `pronomes_1a_pessoa` | eu, me, mim, meu… (autorreferência) | LIWC, categoria *i* (Pennebaker et al., 2015; Boyd et al., 2022); versões brasileiras de Balage Filho, Pardo e Aluísio (2013) e Carvalho et al. (2019) |
| `autodefinicao` | "eu sou", "não sou", "me sinto", "me vejo", "eu como profissional" | enunciados "Eu sou…" do Twenty Statements Test (Kuhn e McPartland, 1954); *identity talk* (Snow e Anderson, 1987); identidades provisórias (Ibarra, 1999); identidade de papel (Stryker e Burke, 2000) |
| `agencia_autoria` | autoria, "o resultado é meu", "fui eu que fiz" | senso de agência e de posse do self mínimo (Gallagher, 2000); posse (Belk, 1988) |
| `self_estendido` | "cérebro externo", "na minha cabeça", "parte de mim", "acessório" | mente estendida (Clark e Chalmers, 1998); self estendido (Belk, 1988, 2013); aspecto estendido do self (Gallagher, 2013) |
| `vocabulario_self` | identidade, essência, autenticidade, autoimagem, autopercepção | self, autoconceito e identidade (Oyserman, Elmore e Smith, 2012; Leary e Tangney, 2012) |
| `self_atribuido_ia` | personalidade e autonomia **da IA** | antropomorfização (Epley, Waytz e Cacioppo, 2007) |

## Decisões (23/10/2026)

- **Os pronomes não servem de semente.** Eles aparecem em metade das frases, e como ponto de partida a vizinhança seria metade do corpus. A pegada deles é medida à parte.
- **"Personalidade" e "autonomia" também não.** No corpus, as duas palavras falam da IA, não do entrevistado.
- **Ficaram de fora** "sozinho" (o sujeito é quase sempre a IA), "meu trabalho" (quase sempre quer dizer "meu emprego") e "humano", "confiar" e "depender". Essas três últimas são candidatas a aparecer *na vizinhança*; como sementes, elas apareceriam no resultado por construção.
- **Elicitação:** o roteiro pergunta sobre autoria, sobre se considerar usuário básico, intermediário ou avançado, sobre "como você se vê" e sobre identidade. Por isso o script marca como elicitada a frase cuja categoria aparece na pergunta anterior do entrevistador.

## Referências

- Balage Filho, P. P., Pardo, T. A. S., & Aluísio, S. M. (2013). An evaluation of the Brazilian Portuguese LIWC dictionary for sentiment analysis. *STIL 2013*. https://aclanthology.org/W13-4829/
- Belk, R. W. (1988). Possessions and the extended self. *Journal of Consumer Research, 15*(2), 139–168.
- Belk, R. W. (2013). Extended self in a digital world. *Journal of Consumer Research, 40*(3), 477–500.
- Boyd, R. L., Ashokkumar, A., Seraj, S., & Pennebaker, J. W. (2022). *The development and psychometric properties of LIWC-22*. University of Texas at Austin.
- Carvalho, F. et al. (2019). Avaliação da versão em português do LIWC 2015 (BP-LIWC2015). *BraSNAM 2019*. https://sol.sbc.org.br/index.php/brasnam/article/download/6545/6441
- Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis, 58*(1), 7–19.
- Epley, N., Waytz, A., & Cacioppo, J. T. (2007). On seeing human: A three-factor theory of anthropomorphism. *Psychological Review, 114*(4), 864–886.
- Gallagher, S. (2000). Philosophical conceptions of the self: Implications for cognitive science. *Trends in Cognitive Sciences, 4*(1), 14–21.
- Gallagher, S. (2013). A pattern theory of self. *Frontiers in Human Neuroscience, 7*, 443.
- Ibarra, H. (1999). Provisional selves: Experimenting with image and identity in professional adaptation. *Administrative Science Quarterly, 44*(4), 764–791.
- Kuhn, M. H., & McPartland, T. S. (1954). An empirical investigation of self-attitudes. *American Sociological Review, 19*(1), 68–76.
- Leary, M. R., & Tangney, J. P. (Eds.). (2012). *Handbook of self and identity* (2nd ed.). Guilford.
- Oyserman, D., Elmore, K., & Smith, G. (2012). Self, self-concept, and identity. In Leary & Tangney (Eds.), *Handbook of self and identity* (pp. 69–104).
- Pennebaker, J. W., Boyd, R. L., Jordan, K., & Blackburn, K. (2015). *The development and psychometric properties of LIWC2015*. University of Texas at Austin.
- Snow, D. A., & Anderson, L. (1987). Identity work among the homeless: The verbal construction and avowal of personal identities. *American Journal of Sociology, 92*(6), 1336–1371.
- Stryker, S., & Burke, P. J. (2000). The past, present, and future of an identity theory. *Social Psychology Quarterly, 63*(4), 284–297.
