export interface Questao {
  id: string
  ano: number
  semestre: number
  disciplina: string
  enunciado: string
  imagens: string[]
  alternativas: Record<string, string>
  gabarito: string
}

export type Pagina = 'home' | 'quiz' | 'resultado'
