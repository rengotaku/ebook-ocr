"""Custom exceptions for book_converter module.

This module defines custom exceptions used throughout the book_converter package.
"""

from __future__ import annotations


class BookConverterError(Exception):
    """Base exception for book_converter module."""


class PageValidationError(BookConverterError):
    """Raised when page validation fails.

    This exception is raised when the output page count is significantly lower
    than the input page count, indicating potential data loss during conversion.

    Attributes:
        input_count: Number of pages in the input
        output_count: Number of pages in the output
        message: Human-readable error message
    """

    def __init__(
        self,
        input_count: int,
        output_count: int,
        message: str | None = None,
    ) -> None:
        """Initialize PageValidationError.

        Args:
            input_count: Number of pages in the input
            output_count: Number of pages in the output
            message: Optional custom message
        """
        self.input_count = input_count
        self.output_count = output_count

        if message is None:
            loss_percent = (
                (input_count - output_count) / input_count * 100
                if input_count > 0
                else 0
            )
            message = (
                f"Page validation failed: {output_count} pages in output vs "
                f"{input_count} pages in input ({loss_percent:.1f}% loss). "
                f"This exceeds the 50% threshold."
            )

        self.message = message
        super().__init__(self.message)
