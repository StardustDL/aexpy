<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NInputGroupLabel, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, VersionIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import { useStore } from '../../services/store'
import { Release, ReleasePair } from '../../models'
import { PairProducer } from '../../services/api'


const props = defineProps<{
    pair: ReleasePair,
}>();

const store = useStore();
const router = useRouter();

const loading = ref<boolean>(false);
const needRefresh = ref<boolean>(true);
const options = ref<SelectOption[]>([]);

async function onProjectChange(value: string) {
    needRefresh.value = true;
    props.pair.new.project = value;
}

async function onFocus() {
    if (!needRefresh.value)
        return;
    loading.value = true;
    try {
        let rels = await store.state.api.generator.releases(props.pair.old.project);
        options.value = rels.map(r => {
            return {
                label: r.version,
                value: r.version
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
    <n-input-group-label size="large">
        <n-icon>
            <ReleaseIcon />
        </n-icon>
    </n-input-group-label>
    <n-input
        v-model:value="pair.old.project"
        placeholder="Project"
        @input="onProjectChange"
        size="large"
    ></n-input>
    <n-input-group-label size="large">
        <n-icon>
            <VersionIcon />
        </n-icon>
    </n-input-group-label>
    <n-select
        v-model:value="pair.old.version"
        filterable
        placeholder="Old Version"
        :options="options"
        :loading="loading"
        @focus="onFocus"
        clearable
        size="large"
    />
    <n-input-group-label size="large">
        <n-icon>
            <VersionIcon />
        </n-icon>
    </n-input-group-label>
    <n-select
        v-model:value="pair.new.version"
        filterable
        placeholder="New Version"
        :options="options"
        :loading="loading"
        @focus="onFocus"
        clearable
        size="large"
    />
</template>