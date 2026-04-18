# React + TypeScript + Vite

이 템플릿은 Vite에서 HMR과 일부 ESLint 규칙을 적용한 React 환경을 최소한으로 구성한 것입니다.

현재 두 가지 공식 플러그인을 사용할 수 있습니다:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) — [Oxc](https://oxc.rs) 사용
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) — [SWC](https://swc.rs/) 사용

## React Compiler

React Compiler는 개발/빌드 성능에 영향을 주기 때문에 이 템플릿에는 기본적으로 활성화되어 있지 않습니다. 활성화하려면 [공식 문서](https://react.dev/learn/react-compiler/installation)를 참고하세요.

## ESLint 설정 확장

프로덕션용 애플리케이션을 개발한다면, 타입 기반 lint 규칙을 활성화하도록 설정을 업데이트하는 것을 권장합니다:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // 다른 설정들...

      // tseslint.configs.recommended를 제거하고 아래로 교체
      tseslint.configs.recommendedTypeChecked,
      // 또는 더 엄격한 규칙을 원하면 아래 사용
      tseslint.configs.strictTypeChecked,
      // 선택적으로 스타일 규칙도 추가 가능
      tseslint.configs.stylisticTypeChecked,

      // 다른 설정들...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // 기타 옵션...
    },
  },
])
```

React 전용 lint 규칙을 위해 [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x)와 [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom)을 설치할 수도 있습니다:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // 다른 설정들...
      // React용 lint 규칙 활성화
      reactX.configs['recommended-typescript'],
      // React DOM용 lint 규칙 활성화
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // 기타 옵션...
    },
  },
])
```
