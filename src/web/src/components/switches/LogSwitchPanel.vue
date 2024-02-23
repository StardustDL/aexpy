<script setup lang="ts">
import { LogIcon } from '../icons';
import { NDrawer, NFlex, NSpin, NLog, useMessage, useLoadingBar, NDrawerContent, NIcon, NTooltip, NSwitch } from 'naive-ui'
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry } from '../../models/description';
import { onMounted, ref, watch, defineModel } from 'vue';
import NotFound from '../NotFound.vue';
import { publicVars } from '../../services/utils'

const value = defineModel({ default: false });
const props = defineProps<{
    load?: () => Promise<string>,
}>();

const message = useMessage();
const loadingbar = useLoadingBar();
const content = ref<string>();
const error = ref<boolean>(false);

async function reload() {
    error.value = false;
    content.value = undefined;
    loadingbar.start();
    try {
        if (props.load) {
            content.value = await props.load();
            publicVars({ "log": content.value });
        } else {
            content.value = "";
        }
        loadingbar.finish();
    }
    catch (e) {
        error.value = true;
        console.error(e);
        loadingbar.error();
        message.error("Failed to load log.");
    }
}

function onShow(shown: boolean) {
    if (!shown || content.value != undefined) return;
    reload();
}
</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-switch v-model:value="value" @update-value="onShow">
                <template #checked>
                    <n-icon size="large" :component="LogIcon" />
                </template>
                <template #unchecked>
                    <n-icon size="large" :component="LogIcon" />
                </template>
            </n-switch>
        </template>
        Log
    </n-tooltip>
    <n-drawer v-model:show="value" :width="600" placement="right">
        <n-drawer-content>
            <template #header>
                <n-flex>
                    <n-icon size="large" :component="LogIcon" />
                    Log
                </n-flex>
            </template>
            <NotFound v-if="error" />
            <n-spin v-else-if="content == undefined" :size="60" style="width: 100%"></n-spin>
            <n-log v-else :log="content" :rows="40" language="log"></n-log>
        </n-drawer-content>
    </n-drawer>
</template>
