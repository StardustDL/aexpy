<script setup lang="ts">
import { NButton, NIcon, NTooltip } from 'naive-ui'
import { SuccIcon, PrevIcon } from '../icons'
import { apiUrl, distributionUrl } from '../../services/utils'
import { Release } from '../../models';
import { useStore } from '../../services/store';
import { computed, onMounted, ref } from 'vue';

const props = defineProps<{
    release: Release,
    kind: "preprocessed" | "extracted"
}>();

const store = useStore();
const items = ref<Release[]>([]);

onMounted(async () => {
    try {
        let data = await store.state.api.package(props.release.project).index();
        items.value = data[props.kind];
    }
    catch (e) {
        console.error("Failed to load product list.", e);
    }
})

const index = computed(() => items.value.findIndex((value, index, arr) => {
    return value.equals(props.release);
}));

const prev = computed(() => {
    if (index.value == -1 || index.value == 0) {
        return null;
    }
    return items.value[index.value - 1];
});

const succ = computed(() => {
    if (index.value == -1 || index.value == items.value.length - 1) {
        return null;
    }
    return items.value[index.value + 1];
});
</script>

<template>
    <router-link :to="kind == 'preprocessed' ? distributionUrl(prev) : apiUrl(prev)" custom v-slot="{ href, navigate }"
        v-if="prev">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-tooltip>
                <template #trigger>
                    <n-icon size="large" :component="PrevIcon" />
                </template>
                {{ prev }}
            </n-tooltip>
        </n-button>
    </router-link>
    <router-link :to="kind == 'preprocessed' ? distributionUrl(succ) : apiUrl(succ)" custom v-slot="{ href, navigate }"
        v-if="succ">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-tooltip>
                <template #trigger>
                    <n-icon size="large" :component="SuccIcon" />
                </template>
                {{ succ }}
            </n-tooltip>
        </n-button>
    </router-link></template>