<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../icons'
import { useRouter } from 'vue-router'
import { useStore } from '../../services/store'
import { Provider, Release } from '../../models'
const props = defineProps<{
    provider: Provider,
}>();

const store = useStore();
const router = useRouter();

const loading = ref<boolean>(false);
const needRefresh = ref<boolean>(true);
const options = ref<SelectOption[]>([]);

async function onFocus() {
    if (!needRefresh.value)
        return;
    loading.value = true;
    try {
        let rels = await store.state.api.generator.providers();
        console.log(rels);
        options.value = rels.map(r => {
            return {
                label: r,
                value: r
            }
        });
    }
    catch {
        options.value = [];
    }
    needRefresh.value = false;
    loading.value = false;
}

</script>

<template>
    <n-select
        v-model:value="provider.name"
        filterable
        placeholder="Provider"
        :options="options"
        :loading="loading"
        @focus="onFocus"
        clearable
    />
</template>