<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NInputGroupLabel, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../icons'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from '../../services/store'
import { Provider, Release } from '../../models'

const store = useStore();
const router = useRouter();
const route = useRoute();

const providers = ref<string[]>([]);
const loading = ref<boolean>(false);
const options = computed(() => {
    return providers.value.map(r => {
        return {
            label: r,
            value: r,
        }
    });
});
const provider = ref("");
const originalProvider = computed(() => {
    for (let pro of providers.value) {
        if (route.fullPath.includes(`/${pro}/`)) {
            return pro;
        }
    }
    return "";
});

onMounted(async () => {
    try {
        providers.value = await store.state.api.generator.providers();
    }
    catch {
    }

    provider.value = originalProvider.value;
});


</script>

<template>
    <n-input-group>
        <n-input-group-label size="small">
            <n-icon>
                <ProviderIcon />
            </n-icon>
        </n-input-group-label>
        <n-select
            v-model:value="provider"
            filterable
            placeholder="Provider"
            :options="options"
            :loading="loading"
            clearable
            size="small"
        />
        <n-button
            size="small"
            tag="a"
            :href="route.fullPath.replace(`/${originalProvider}/`, `/${provider}/`)"
            target="_blank"
        >
            <template #icon>
                <n-icon>
                    <GoIcon />
                </n-icon>
            </template>
        </n-button>
    </n-input-group>
</template>