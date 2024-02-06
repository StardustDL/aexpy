<script setup lang="ts">
import { NIcon, NTime, NFlex, NTooltip, NTag, NAvatar, NText } from 'naive-ui'
import { FaceId, FaceIdError } from '@vicons/tabler'
import { ProduceState } from '../../models';

const props = defineProps<{
    state: ProduceState,
}>();

</script>

<template>
    <n-tag :type="props.state == ProduceState.Success ? 'success' : 'error'">
        <template #avatar>
            <n-icon size="medium">
                <FaceId v-if="props.state == ProduceState.Success" />
                <FaceIdError v-else />
            </n-icon>
        </template>
        {{ ProduceState[props.state] }}
    </n-tag>
</template>