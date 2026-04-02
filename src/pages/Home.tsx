import { QUESTOES_POR_DISCIPLINA } from '../config'
import type { Questao } from '../types'

const DISCIPLINAS = Object.keys(QUESTOES_POR_DISCIPLINA)

interface Props {
  questoes: Questao[]
  onIniciar: (disciplina: string) => void
}

export default function Home({ questoes, onIniciar }: Props) {
  const contagem = (disc: string) => questoes.filter(q => q.disciplina === disc).length

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Simulador UFU</h1>
      <p className="text-gray-500 mb-10">Escolha uma disciplina para começar</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 w-full max-w-3xl">
        {DISCIPLINAS.map(disc => {
          const total = contagem(disc)
          const simulado = QUESTOES_POR_DISCIPLINA[disc]
          return (
            <button
              key={disc}
              onClick={() => total > 0 && onIniciar(disc)}
              disabled={total === 0}
              className={`
                rounded-xl p-5 text-left border transition-all
                ${total > 0
                  ? 'bg-white border-gray-200 hover:border-indigo-400 hover:shadow-md hover:scale-[1.02] cursor-pointer'
                  : 'bg-gray-100 border-gray-100 opacity-50 cursor-not-allowed'}
              `}
            >
              <div className="font-semibold text-gray-800">{disc}</div>
              <div className="text-sm text-gray-400 mt-1">
                {total > 0
                  ? <>{simulado} questões por simulado <span className="text-gray-300">·</span> {total} no banco</>
                  : 'sem questões'}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
