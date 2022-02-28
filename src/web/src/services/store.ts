import { InjectionKey } from 'vue'
import { createStore, useStore as baseUseStore, Store } from 'vuex'
import { Api } from './api';

export interface State {
    api: Api;
}

export const key: InjectionKey<Store<State>> = Symbol()

const defaultApiUrl = import.meta.env.DEV ? "http://localhost:5000/api" : "/api";

export const store = createStore<State>({
    state() {
        return {
            api: new Api(defaultApiUrl),
        }
    },
    mutations: {
        setApiUrl(state, value: string) {
            state.api = new Api(value);
        },
    }
})

export function useStore() {
    return baseUseStore(key)
}