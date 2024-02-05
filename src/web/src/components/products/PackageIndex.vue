<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent, reactive } from 'vue'
import { NSpace, NSpin, NIcon, NButton, useMessage } from 'naive-ui'
import { PackageIcon } from '../icons'
import { useStore } from '../../services/store'

const message = useMessage();
const store = useStore();

const packages = ref<string[] | undefined>();

onMounted(async () => {
    try {
        packages.value = await store.state.api.packages();
    }
    catch (e) {
        console.error(e);
        message.error(`Failed to load package index.`);
    }
});

</script>

<template>
    <n-space v-if="packages">
        <n-button v-for="item in packages" :key="item" text tag="a" :href="`/packages/${item}`" target="_blank">
            <template #icon>
                <n-icon>
                    <PackageIcon />
                </n-icon>
            </template>
            {{ item }}</n-button>
    </n-space>
    <n-spin :size="40" v-else/>
</template>
