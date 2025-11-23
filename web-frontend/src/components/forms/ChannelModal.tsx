import {
  Button,
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
  Stack,
  Textarea,
} from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import type { ChannelFormInput } from '../../api/types';

interface ChannelModalProps {
  isOpen: boolean;
  mode: 'create' | 'edit';
  initialValue?: ChannelFormInput;
  onClose: () => void;
  onSubmit: (payload: ChannelFormInput) => Promise<void>;
}

const defaultForm: ChannelFormInput = { slug: '', title: '' };

export function ChannelModal({ isOpen, mode, initialValue, onClose, onSubmit }: ChannelModalProps) {
  const [form, setForm] = useState<ChannelFormInput>(initialValue ?? defaultForm);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setForm(initialValue ?? defaultForm);
    }
  }, [isOpen, initialValue]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(form);
      if (mode === 'create') {
        setForm(defaultForm);
      }
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  const header = mode === 'create' ? '채널 추가' : '채널 수정';
  const buttonLabel = mode === 'create' ? '생성' : '수정';

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{header}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>Slug</FormLabel>
              <Input
                value={form.slug}
                isDisabled={mode === 'edit'}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
                placeholder="예: rw_test2"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>제목</FormLabel>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="채널 제목" />
            </FormControl>
            <FormControl>
              <FormLabel>설명</FormLabel>
              <Textarea
                value={form.description ?? ''}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="선택 입력"
              />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            취소
          </Button>
          <Button colorScheme="purple" onClick={handleSubmit} isLoading={submitting}>
            {buttonLabel}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
