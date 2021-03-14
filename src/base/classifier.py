from torch import Tensor
from torch.nn import Module, EmbeddingBag, Linear


class Classifier(Module):

    embedding_bag: EmbeddingBag
    linear: Linear

    def __init__(self, vocab_size: int, emb_size: int, class_count: int):
        super().__init__()

        self.embedding_bag = EmbeddingBag(num_embeddings=vocab_size, embedding_dim=emb_size)
        self.linear = Linear(emb_size, class_count)

    def forward(self, tok_lists_batch: Tensor) -> Tensor:
        """
        :param tok_lists_batch: (batch_size, sent_count, sent_len)
        :return: (batch_size, class_count)
        """

        # Concat entity's sentences to a single context
        #
        # < tok_lists_batch  (batch_size, sent_count, sent_len)
        # > tok_list_batch   (batch_size, sent_count * sent_len)

        batch_size, sent_count, sent_len = tok_lists_batch.shape

        tok_list_batch = tok_lists_batch.reshape(batch_size, sent_count * sent_len)

        # Embed context
        #
        # < tok_list_batch  (batch_size, sent_count * sent_len)
        # > ctxt_batch      (batch_size, emb_size)

        ctxt_batch = self.embedding_bag(tok_list_batch)

        # Push context through linear layer
        #
        # < ctxt_batch    (batch_size, emb_size)
        # > logits_batch  (batch_size, class_count)

        logits_batch = self.linear(ctxt_batch)

        return logits_batch
