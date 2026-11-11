// 顺序练习进度：按“学员 + 分类”分别记住上次做到的位置
const currentUserKey = () => {
  try {
    const info = JSON.parse(localStorage.getItem('userInfo') || '{}')
    return info.id || info.username || 'guest'
  } catch (e) {
    return 'guest'
  }
}

const storageKey = (categoryId) => `practice_progress_${currentUserKey()}_${categoryId || 0}_order`

export function getPracticeOffset(categoryId) {
  const value = Number(localStorage.getItem(storageKey(categoryId)) || 0)
  return Number.isFinite(value) && value > 0 ? value : 0
}

export function savePracticeOffset(categoryId, offset) {
  const value = Number(offset || 0)
  localStorage.setItem(storageKey(categoryId), String(value > 0 ? value : 0))
}

export function clearPracticeOffset(categoryId) {
  localStorage.removeItem(storageKey(categoryId))
}
