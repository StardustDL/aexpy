<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent, reactive } from 'vue'
import { NFlex, NSpin, NIcon, NButton, useMessage, NCard } from 'naive-ui'
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
    <n-flex v-if="packages" size="large">
        <n-button v-for="item in packages" :key="item" text tag="a" :href="`/packages/${item}`" size="large">
            <template #icon>
                <n-icon size="large">
                    <PackageIcon />
                </n-icon>
            </template>
            {{ item }}
        </n-button>
    </n-flex>
    <n-spin :size="40" v-else />
</template>
