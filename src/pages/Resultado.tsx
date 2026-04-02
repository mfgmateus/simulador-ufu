import { useState } from 'react'
import type { Questao } from '../types'

interface Props {
  disciplina: string
  questoes: Questao[]
  respostas: Record<string, string>
  onReiniciar: () => void
  onVoltar: () => void
}

const LETRAS = ['A', 'B', 'C', 'D', 'E']

export default function Resultado({ disciplina, questoes, respostas, onReiniciar, onVoltar }: Props) {
  const [revisando, setRevisando] = useState(false)

  const acertos = questoes.filter(q => respostas[q.id] === q.gabarito && q.gabarito).length
  const total = questoes.length
  const pct = Math.round((acertos / total) * 100)
  const nota = pct >= 70 ? 'Muito bem!' : pct >= 50 ? 'Bom resultado' : 'Continue estudando'

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4">
      {!revisando ? (
        <>
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10 max-w-sm w-full text-center mb-8">
            <p className="text-gray-400 text-sm mb-1">{disciplina}</p>
            <div className="text-6xl font-bold text-indigo-500 my-4">
              {acertos}<span className="text-3xl text-gray-300">/{total}</span>
            </div>
            <div className="text-2xl font-semibold text-gray-800 mb-1">{pct}%</div>
            <p className="text-gray-400 text-sm">{nota}</p>
          </div>

          <div className="flex gap-3 flex-wrap justify-center">
            <button onClick={() => setRevisando(true)} className="px-6 py-3 rounded-xl bg-white border border-gray-200 hover:border-gray-300 text-gray-700 text-sm font-medium shadow-sm">
              Revisar questões
            </button>
            <button onClick={onReiniciar} className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium shadow-sm">
              Tentar novamente
            </button>
            <button onClick={onVoltar} className="px-6 py-3 rounded-xl bg-white border border-gray-200 hover:border-gray-300 text-gray-700 text-sm font-medium shadow-sm">
              Escolher disciplina
            </button>
          </div>
        </>
      ) : (
        <div className="w-full max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-800">Revisão — {disciplina}</h2>
            <button onClick={() => setRevisando(false)} className="text-gray-400 hover:text-gray-600 text-sm">
              ← Voltar ao resultado
            </button>
          </div>

          <div className="flex flex-col gap-6">
            {questoes.map((q, i) => {
              const resp = respostas[q.id]
              const acertou = resp === q.gabarito && !!q.gabarito
              return (
                <div key={q.id} className={`rounded-2xl p-5 border ${acertou ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <p className="text-xs text-gray-400 mb-2">Questão {i + 1}</p>
                  <p className="text-sm text-gray-700 leading-relaxed mb-4 whitespace-pre-wrap">{q.enunciado}</p>

                  {q.imagens.length > 0 && (
                    <div className="mb-4 flex flex-col gap-2">
                      {q.imagens.map(img => (
                        <img key={img} src={`${import.meta.env.BASE_URL}images/${img}`} alt="" className="max-w-full rounded-lg border border-gray-200" />
                      ))}
                    </div>
                  )}

                  <div className="flex flex-col gap-2">
                    {LETRAS.filter(l => q.alternativas[l]).map(letra => {
                      const isGabarito = letra === q.gabarito
                      const isErro = letra === resp && !acertou
                      let cls = 'bg-white border border-gray-200 text-gray-600'
                      if (isGabarito) cls = 'bg-green-600 border-green-600 text-white'
                      else if (isErro) cls = 'bg-red-500 border-red-500 text-white'
                      return (
                        <div key={letra} className={`rounded-lg px-4 py-2 flex gap-3 text-sm ${cls}`}>
                          <span className="font-bold w-4 shrink-0">{letra}</span>
                          <span>{q.alternativas[letra]}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex gap-3 mt-8 justify-center">
            <button onClick={onReiniciar} className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium">
              Tentar novamente
            </button>
            <button onClick={onVoltar} className="px-6 py-3 rounded-xl bg-white border border-gray-200 hover:border-gray-300 text-gray-700 text-sm font-medium">
              Escolher disciplina
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
