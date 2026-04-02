import { useEffect, useState } from 'react'
import type { Questao, Pagina } from './types'
import { QUESTOES_POR_DISCIPLINA } from './config'
import Home from './pages/Home'
import Quiz from './pages/Quiz'
import Resultado from './pages/Resultado'

function embaralhar<T>(arr: T[]): T[] {
  return [...arr].sort(() => Math.random() - 0.5)
}

export default function App() {
  const [questoes, setQuestoes] = useState<Questao[]>([])
  const [pagina, setPagina] = useState<Pagina>('home')
  const [disciplina, setDisciplina] = useState('')
  const [questoesDisciplina, setQuestoesDisciplina] = useState<Questao[]>([])
  const [respostas, setRespostas] = useState<Record<string, string>>({})

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}questions.json`)
      .then(r => r.json())
      .then(setQuestoes)
  }, [])

  function iniciar(disc: string) {
    const limite = QUESTOES_POR_DISCIPLINA[disc] ?? 5
    const qs = embaralhar(questoes.filter(q => q.disciplina === disc)).slice(0, limite)
    setDisciplina(disc)
    setQuestoesDisciplina(qs)
    setRespostas({})
    setPagina('quiz')
  }

  function finalizar(resp: Record<string, string>) {
    setRespostas(resp)
    setPagina('resultado')
  }

  if (pagina === 'quiz') {
    return (
      <Quiz
        disciplina={disciplina}
        questoes={questoesDisciplina}
        onFinalizar={finalizar}
        onVoltar={() => setPagina('home')}
      />
    )
  }

  if (pagina === 'resultado') {
    return (
      <Resultado
        disciplina={disciplina}
        questoes={questoesDisciplina}
        respostas={respostas}
        onReiniciar={() => iniciar(disciplina)}
        onVoltar={() => setPagina('home')}
      />
    )
  }

  return <Home questoes={questoes} onIniciar={iniciar} />
}
