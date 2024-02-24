<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'
import { SuccIcon, PrevIcon } from '../icons'
import { apiUrl, changeUrl } from '../../services/utils'
import { ReleasePair } from '../../models';
import { useStore } from '../../services/store';
import { computed, onMounted, ref } from 'vue';

const props = defineProps<{
    pair: ReleasePair
}>();

const store = useStore();
const items = ref<ReleasePair[]>([]);

onMounted(async () => {
    try {
        if (!props.pair.sameProject()) {
            throw new Error(`Not same project: ${props.pair}`);
        }
        let data = await store.state.api.package(props.pair.old.project).index();
        items.value = data.diffed;
    }
    catch (e) {
        console.error("Failed to load product list.", e);
    }
})

const index = computed(() => items.value.findIndex((value, index, arr) => {
    return value.equals(props.pair);
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
    <router-link :to="changeUrl(prev)" custom v-slot="{ href, navigate }" v-if="prev">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-icon size="large" :component="PrevIcon" />
        </n-button>
    </router-link>
    <router-link :to="changeUrl(succ)" custom v-slot="{ href, navigate }" v-if="succ">
        <n-button tag="a" :href="href" @click="navigate" type="info" ghost>
            <n-icon size="large" :component="SuccIcon" />
        </n-button>
    </router-link>
</template>