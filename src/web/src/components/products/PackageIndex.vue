<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent, reactive } from 'vue'
import { NFlex, NSpin, NIcon, NButton, useMessage, NCard } from 'naive-ui'
import { PackageIcon } from '../icons'
import { useStore } from '../../services/store'
import { projectUrl } from '../../services/utils'
import NotFound from '../NotFound.vue';

const message = useMessage();
const store = useStore();

const packages = ref<string[] | undefined>();
const error = ref<boolean>(false);

onMounted(async () => {
    try {
        packages.value = await store.state.api.packages();
    }
    catch (e) {
        error.value = true;
        console.error(e);
        message.error(`Failed to load package index.`);
    }
});

</script>

<template>
    <n-flex v-if="packages && !error" size="large">
        <router-link v-for="item in packages" :key="item" :to="projectUrl(item)" custom v-slot="{ href, navigate }">
            <n-button text tag="a" :href="href" @click="navigate" size="large">
                <template #icon>
                    <n-icon size="large" :component="PackageIcon" />
                </template>
                {{ item }}
            </n-button>
        </router-link>
    </n-flex>
    <n-spin :size="40" v-if="!packages && !error" />
    <NotFound v-if="error" path="/"/>
</template>
