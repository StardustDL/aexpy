<script setup lang="ts">
import { NIcon, NButton, NDropdown } from 'naive-ui'
import { ProduceMode } from '../../models';
import { useRouter } from 'vue-router'
import { GoIcon } from '../icons';

const props = defineProps<{
    url: string,
    type?: 'default' | 'tertiary' | 'primary' | 'info' | 'success' | 'warning' | 'error',
    query?: any,
}>();

const router = useRouter();

const options = [
    {
        label: "Cache",
        key: ProduceMode.Read,
    },
    {
        label: "Redo",
        key: ProduceMode.Write,
    }
];

function onGo() {
    router.push({
        path: `${props.url}`,
        query: {
            mode: ProduceMode.Access,
            ...(props.query ?? {})
        }
    });
}

function handleSelect(key: ProduceMode) {
    router.push({
        path: `${props.url}`,
        query: {
            mode: key,
            ...props.query
        }
    });
}

</script>

<template>
    <n-dropdown trigger="hover" :options="options" @select="handleSelect" size="large" show-arrow>
        <n-button :type="type ?? 'primary'" @click="onGo" :style="{ width: '10%' }" size="large">
            <n-icon size="large">
                <slot>
                    <GoIcon />
                </slot>
            </n-icon>
        </n-button>
    </n-dropdown>

</template>