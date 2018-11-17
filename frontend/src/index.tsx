import * as React from 'react';
import * as ReactDOM from 'react-dom';
import './index.css';
import registerServiceWorker from './registerServiceWorker';
import { createStore } from 'redux';
import { enthusiasm } from './reducers/index';
import { EnthusiasmAction } from './actions/index'
import { IStoreState } from './types/index';
import Hello from './containers/Hello';
import { Provider } from 'react-redux';
import { DatePicker } from 'antd';


const store = createStore<IStoreState, EnthusiasmAction, any, any>(enthusiasm, {
  enthusiasmLevel: 1,
  languageName: 'TypeScript',
});

ReactDOM.render(
  <Provider store={store}>
    <Hello />
  </Provider>,
  document.getElementById('root') as HTMLElement
);
ReactDOM.render(<DatePicker />, document.getElementById('DatePicker') as HTMLElement);


registerServiceWorker();
