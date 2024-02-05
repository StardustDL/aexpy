import { InjectionKey } from 'vue'
import { createStore, useStore as baseUseStore, Store } from 'vuex'
import { Api } from './api';

export interface State {
    api: Api;
}

export const key: InjectionKey<Store<State>> = Symbol()

const defaultApiUrl = import.meta.env.DEV ? "http://localhost:8008/api" : "https://stardustdl-labs.github.io/aexpy-index";

export const store = createStore<State>({
    state() {
        let apiUrl = window.localStorage.getItem("apiUrl") ?? defaultApiUrl;
        let api = new Api(apiUrl);
        (<any>window).api = api;
        return {
            api: api,
        }
    },
    mutations: {
        setApiUrl(state, value: string) {
            state.api = new Api(value);
            (<any>window).api = state.api;
            window.localStorage.setItem("apiUrl", value);
        },
    }
})

export function useStore() {
    return baseUseStore(key)
}