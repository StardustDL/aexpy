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
        let apiUrl = window.localStorage.getItem("apiUrl") ?? defaultApiUrl;
        return {
            api: new Api(apiUrl),
        }
    },
    mutations: {
        setApiUrl(state, value: string) {
            state.api = new Api(value);
            window.localStorage.setItem("apiUrl", value);
        },
    }
})

export function useStore() {
    return baseUseStore(key)
}