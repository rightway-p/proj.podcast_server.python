import {
  Button,
  Checkbox,
  CheckboxGroup,
  FormControl,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Stack,
  Switch,
  Text,
} from '@chakra-ui/react';
import { useEffect, useMemo, useState } from 'react';
import type { ScheduleFormInput, Playlist, Schedule } from '../../api/types';

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  playlist: Playlist | null;
  mode: 'create' | 'edit';
  schedule?: Schedule | null;
  onSubmit: (payload: ScheduleFormInput, scheduleId?: number) => Promise<void>;
  onDelete?: (scheduleId: number) => Promise<void>;
}

export function ScheduleModal({
  isOpen,
  onClose,
  playlist,
  mode,
  schedule,
  onSubmit,
  onDelete,
}: ScheduleModalProps) {
  const dayOptions = useMemo(
    () => [
      { value: 'mon', label: '월' },
      { value: 'tue', label: '화' },
      { value: 'wed', label: '수' },
      { value: 'thu', label: '목' },
      { value: 'fri', label: '금' },
      { value: 'sat', label: '토' },
      { value: 'sun', label: '일' },
    ],
    [],
  );

  const buildInitialForm = () => ({
    playlist_id: playlist?.id ?? schedule?.playlist_id ?? 0,
    days_of_week: schedule?.days_of_week ?? ['mon', 'tue', 'wed', 'thu', 'fri'],
    run_time: schedule?.run_time ?? '07:00',
    timezone: schedule?.timezone ?? 'Asia/Seoul',
    is_active: schedule?.is_active ?? true,
  });

  const [form, setForm] = useState<ScheduleFormInput>(buildInitialForm);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const resetForm = () => {
    setForm(buildInitialForm());
  };

  useEffect(() => {
    resetForm();
  }, [playlist, schedule, isOpen]);

  const handleSubmit = async () => {
    if (!form.days_of_week.length || !playlist) {
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit({ ...form, playlist_id: playlist.id }, schedule?.id);
      resetForm();
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!schedule || !onDelete) {
      return;
    }
    if (!window.confirm('선택한 스케줄을 삭제할까요?')) {
      return;
    }
    setDeleting(true);
    try {
      await onDelete(schedule.id);
      resetForm();
      onClose();
    } finally {
      setDeleting(false);
    }
  };

  const isEditMode = mode === 'edit';

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{isEditMode ? '스케줄 수정' : '스케줄 추가'}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl>
              <FormLabel>플레이리스트</FormLabel>
              <Text fontSize="sm" color="gray.500">
                {playlist ? playlist.title || playlist.youtube_playlist_id : '선택된 플레이리스트가 없습니다.'}
              </Text>
            </FormControl>
            <FormControl isRequired>
              <FormLabel>요일</FormLabel>
              <CheckboxGroup
                value={form.days_of_week}
                onChange={(values) => setForm({ ...form, days_of_week: values as string[] })}
              >
                <SimpleGrid columns={3} spacing={1}>
                  {dayOptions.map((option) => (
                    <Checkbox key={option.value} value={option.value}>
                      {option.label}
                    </Checkbox>
                  ))}
                </SimpleGrid>
              </CheckboxGroup>
              {form.days_of_week.length === 0 ? (
                <Text fontSize="xs" color="red.500" mt={2}>
                  최소 한 개의 요일을 선택하세요.
                </Text>
              ) : null}
            </FormControl>
            <FormControl isRequired>
              <FormLabel>실행 시각</FormLabel>
              <Input value={form.run_time} onChange={(e) => setForm({ ...form, run_time: e.target.value })} placeholder="07:00" />
            </FormControl>
            <FormControl>
              <FormLabel>타임존</FormLabel>
              <Input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">활성</FormLabel>
              <Switch isChecked={form.is_active ?? true} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter justifyContent="space-between">
          {isEditMode && schedule && onDelete ? (
            <Button colorScheme="red" variant="ghost" onClick={handleDelete} isLoading={deleting}>
              삭제
            </Button>
          ) : (
            <span />
          )}
          <Stack direction="row" spacing={3} align="center">
            <Button variant="ghost" onClick={onClose}>
              취소
            </Button>
            <Button colorScheme="purple" onClick={handleSubmit} isLoading={submitting} isDisabled={!playlist}>
              {isEditMode ? '저장' : '생성'}
            </Button>
          </Stack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
